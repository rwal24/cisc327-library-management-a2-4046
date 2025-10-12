import importlib
from datetime import datetime, timedelta

import pytest

# We import the modules after monkeypatching DB path in the fixture below.
# (Pytest will inject fixtures by name into test functions.)


@pytest.fixture()
def fixed_now():
    # A deterministic "now" for all time-sensitive logic
    return datetime(2025, 1, 15, 12, 0, 0)


@pytest.fixture()
def db_setup(tmp_path, monkeypatch, fixed_now):
    """
    Create an isolated temp SQLite file, point the database module to it,
    initialize schema + sample data, and freeze datetime in both modules.
    """
    # Import database first so we can patch its globals before anything else imports it
    import database as db

    # Point to a temporary on-disk DB (':memory:' would create a new DB per connection)
    temp_db_path = tmp_path / "test_library.db"
    monkeypatch.setattr(db, "DATABASE", str(temp_db_path))

    # Freeze database.datetime.now() to fixed_now
    class _FixedDateTimeDB(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(db, "datetime", _FixedDateTimeDB)

    # Initialize tables and sample data
    db.init_database()
    db.add_sample_data()

    # Now import library_service (after DB is configured)
    import library_service as svc

    # Freeze library_service.datetime.now() to fixed_now
    class _FixedDateTimeSVC(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now if tz is None else fixed_now.astimezone(tz)

    monkeypatch.setattr(svc, "datetime", _FixedDateTimeSVC)

    # Hand back references for convenience in tests
    return {"db": db, "svc": svc, "fixed_now": fixed_now}


# ----------------------------
# add_book_to_catalog
# ----------------------------

def test_add_book_to_catalog_success(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]

    ok, msg = svc.add_book_to_catalog(
        title="Clean Code",
        author="Robert C. Martin",
        isbn="9780132350884",
        total_copies=2,
    )
    assert ok is True
    assert "successfully added" in msg.lower()

    # Verify it exists
    saved = db.get_book_by_isbn("9780132350884")
    assert saved is not None
    assert saved["title"] == "Clean Code"
    assert saved["available_copies"] == 2


@pytest.mark.parametrize(
    "title,author,isbn,total_copies,expected_msg_fragment",
    [
        ("", "Some One", "9781234567890", 1, "Title is required"),
        ("A"*201, "Some One", "9781234567890", 1, "Title must be less"),
        ("Valid", "", "9781234567890", 1, "Author is required"),
        ("Valid", "A"*101, "9781234567890", 1, "Author must be less"),
        ("Valid", "Auth", "978123", 1, "ISBN must be exactly 13 digits"),
        ("Valid", "Auth", "97 81234567890", 1, "ISBN must be exactly 13 digits"),
        ("Valid", "Auth", "9781234567890", 0, "Total copies must be a positive"),
        ("Valid", "Auth", "9781234567890", -1, "Total copies must be a positive"),
    ],
)
def test_add_book_to_catalog_validation(db_setup, title, author, isbn, total_copies, expected_msg_fragment):
    svc = db_setup["svc"]

    ok, msg = svc.add_book_to_catalog(title, author, isbn, total_copies)
    assert ok is False
    assert expected_msg_fragment.lower() in msg.lower()


def test_add_book_to_catalog_duplicate_isbn(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]

    # Use an ISBN from the sample data: e.g., "1984" is 9780451524935
    existing = db.get_book_by_isbn("9780451524935")
    assert existing is not None

    ok, msg = svc.add_book_to_catalog(
        title="Different Title",
        author="Different Author",
        isbn="9780451524935",
        total_copies=1,
    )
    assert ok is False
    assert "already exists" in msg.lower()


# ----------------------------
# borrow_book_by_patron
# ----------------------------

def _get_any_available_book(db):
    for b in db.get_all_books():
        if b["available_copies"] > 0:
            return b
    return None


def test_borrow_book_by_patron_success(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]

    book = _get_any_available_book(db)
    assert book is not None, "Expected at least one available book in sample data."

    ok, msg = svc.borrow_book_by_patron("654321", book["id"])
    assert ok is True
    assert "successfully borrowed" in msg.lower()

    # Availability should decrease by 1
    updated = db.get_book_by_id(book["id"])
    assert updated["available_copies"] == book["available_copies"] - 1


def test_borrow_book_by_patron_invalid_inputs(db_setup):
    svc = db_setup["svc"]

    ok, msg = svc.borrow_book_by_patron("12", 1)
    assert ok is False and "invalid patron id" in msg.lower()

    ok, msg = svc.borrow_book_by_patron("123456", 99999)
    assert ok is False and "book not found" in msg.lower()


def test_borrow_book_by_patron_limit_enforced(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]

    # Create 5 separate books for this patron to reach the limit
    base_isbn = 9790000000000
    for i in range(5):
        assert db.insert_book(
            f"Book {i}", f"Author {i}", str(base_isbn + i), 1, 1
        )

        # borrow each
        # find its id by ISBN then borrow
        book = db.get_book_by_isbn(str(base_isbn + i))
        ok, _ = svc.borrow_book_by_patron("111111", book["id"])
        assert ok is True

    # Now try to borrow a 6th
    extra_ok, extra_msg = svc.borrow_book_by_patron("111111", _get_any_available_book(db)["id"])
    assert extra_ok is False
    assert "maximum borrowing limit of 5" in extra_msg.lower()


# ----------------------------
# calculate_late_fee_for_book
# ----------------------------

def _make_borrow(db, patron, book_id, borrow_date, due_date):
    assert db.insert_borrow_record(patron, book_id, borrow_date, due_date)
    assert db.update_book_availability(book_id, -1)


def test_calculate_late_fee_no_overdue(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]
    now = db_setup["fixed_now"]

    # Pick/insert a fresh book to control dates
    isbn = "9780000000001"
    assert db.insert_book("T0", "A0", isbn, 1, 1)
    book = db.get_book_by_isbn(isbn)

    _make_borrow(db, "222222", book["id"], now - timedelta(days=2), now + timedelta(days=5))

    fee = svc.calculate_late_fee_for_book("222222", book["id"])
    assert fee["fee_amount"] == 0.0
    assert fee["days_overdue"] == 0
    assert "no late fee" in fee["status"].lower()


@pytest.mark.parametrize(
    "days_over,expected_fee",
    [
        (3, 1.5),   # 0.5/day up to 7
        (7, 3.5),   # 7 * 0.5
        (10, 6.5),  # 3.5 + (10-7)
        (18, 14.5), # 3.5 + 11
        (25, 15.0), # capped
    ],
)
def test_calculate_late_fee_tiers(db_setup, days_over, expected_fee):
    svc = db_setup["svc"]
    db = db_setup["db"]
    now = db_setup["fixed_now"]

    isbn = f"9780000000{100+days_over:03d}"
    assert db.insert_book(f"T{days_over}", "AX", isbn, 1, 1)
    book = db.get_book_by_isbn(isbn)

    _make_borrow(db, "333333", book["id"], now - timedelta(days=30), now - timedelta(days=days_over))

    fee = svc.calculate_late_fee_for_book("333333", book["id"])
    assert fee["days_overdue"] == days_over
    assert fee["fee_amount"] == pytest.approx(expected_fee, rel=1e-9)
    assert "after the due date" in fee["status"].lower()


def test_calculate_late_fee_input_errors(db_setup):
    svc = db_setup["svc"]

    # Bad patron id
    out = svc.calculate_late_fee_for_book("12", 1)
    assert out["status"].lower().startswith("patron id")

    # Non-existent book
    out = svc.calculate_late_fee_for_book("123456", 99999)
    assert "does not exist" in out["status"].lower()

    # Book not borrowed by user
    out = svc.calculate_late_fee_for_book("444444", 1)
    assert "not borrowed" in out["status"].lower()


# ----------------------------
# search_books_in_catalog
# ----------------------------

def test_search_books_by_author_title_isbn(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]

    # Ensure a known title/author/isbn in DB
    assert db.insert_book("Refactoring", "Martin Fowler", "9780201485677", 2, 2)

    # Author (substring, case-insensitive)
    res = svc.search_books_in_catalog("martin", "author")
    assert any("Martin Fowler" == b["author"] for b in res)

    # Title (substring, case-insensitive)
    res = svc.search_books_in_catalog("refactor", "title")
    assert any("Refactoring" == b["title"] for b in res)

    # ISBN (exact, 13 digits)
    res = svc.search_books_in_catalog("9780201485677", "isbn")
    assert len(res) == 1 and res[0]["title"] == "Refactoring"


def test_search_books_invalid_inputs(db_setup):
    svc = db_setup["svc"]

    # Non-str inputs return []
    assert svc.search_books_in_catalog(123, "author") == []
    assert svc.search_books_in_catalog("test", 456) == []

    # Bad search type
    assert svc.search_books_in_catalog("test", "publisher") == []

    # Empty search term
    assert svc.search_books_in_catalog("", "title") == []

    # ISBN must be exactly 13 digits
    assert svc.search_books_in_catalog("12345", "isbn") == []


# ----------------------------
# get_patron_status_report
# ----------------------------

def test_get_patron_status_report_structure_and_totals(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]
    now = db_setup["fixed_now"]

    # Prepare: 2 borrows for patron, one overdue by 3 days (fee 1.5), one not overdue
    assert db.insert_book("Soon™", "Dev", "9781111111111", 1, 1)
    assert db.insert_book("Yesterday", "Ops", "9782222222222", 1, 1)

    b1 = db.get_book_by_isbn("9781111111111")
    b2 = db.get_book_by_isbn("9782222222222")

    # Not overdue: due in +2 days
    _make_borrow(db, "555555", b1["id"], now - timedelta(days=1), now + timedelta(days=2))
    # Overdue: due 3 days ago
    _make_borrow(db, "555555", b2["id"], now - timedelta(days=10), now - timedelta(days=3))

    report = svc.get_patron_status_report("555555")
    assert set(report.keys()) == {
        "patron_id", "currently_borrowed", "owed_late_fees",
        "current_borrow_count", "history", "status"
    }
    assert report["patron_id"] == "555555"
    assert report["current_borrow_count"] == 2
    # Owed late fees should be 1.5 (3 days * $0.5)
    assert report["owed_late_fees"] == pytest.approx(1.5, rel=1e-9)
    # currently_borrowed contains tuples (title, due_date)
    assert any(t[0] == "Yesterday" for t in report["currently_borrowed"])


# ----------------------------
# return_book_by_patron (known-bug placeholder test)
# ----------------------------

@pytest.mark.xfail(reason="Known bug in return_book_by_patron: quoting error in f-string and incomplete logic.")
def test_return_book_by_patron_flow(db_setup):
    svc = db_setup["svc"]
    db = db_setup["db"]
    now = db_setup["fixed_now"]

    # Create a borrow that is not overdue to exercise the "normal" return path
    assert db.insert_book("Returnable", "Unit Tester", "9783333333333", 1, 1)
    bk = db.get_book_by_isbn("9783333333333")
    assert bk["available_copies"] == 1

    # Borrow it
    assert svc.borrow_book_by_patron("666666", bk["id"])[0] is True

    # Try to return it
    ok, msg = svc.return_book_by_patron("666666", bk["id"])
    assert ok is True
    # Verify availability incremented
    updated = db.get_book_by_id(bk["id"])
    assert updated["available_copies"] == 1
