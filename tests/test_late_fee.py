from services.library_service import add_book_to_catalog, borrow_book_by_patron, return_book_by_patron, calculate_late_fee_for_book
from database import init_database, get_book_by_isbn
import pytest

# Note: since return_book_by_patron is not implemented, the return dictionary will be made up here
# Placeholder return values expected since function is not fully implemented

def reset_db():
    from pathlib import Path
    Path("library.db").unlink(missing_ok=True)
    init_database()

reset_db()
add_book_to_catalog("Book Test", "Author Test", "9087654321099", 100)

Book_test_id = get_book_by_isbn("9087654321099")["id"]

# **************** Negative Test Cases ****************

def test_calculate_late_fee_for_non_existent_book():
    # attempt to calculate return fee for a book that does not exist
    results = calculate_late_fee_for_book("111100", 200)

    assert results["fee_amount"] == 0.0
    assert results["days_overdue"] == 0
    assert "Book does not exist" in results["status"]


def test_calculate_late_fee_for_book_not_borowed_book():
    # attempt to calculate return fee for a book where book exists but was not borrowed
    add_book_to_catalog("Book Test 2", "Author Test 2", "9087654321091", 1)
    Book_test_id_two = get_book_by_isbn("9087654321091")["id"]
    borrow_book_by_patron("222200", Book_test_id_two)
    return_book_by_patron("222200", Book_test_id_two)
    results = calculate_late_fee_for_book("222200", Book_test_id)

    assert results["fee_amount"] == 0.0
    assert results["days_overdue"] == 0
    assert "not borrowed" in results["status"]


def test_calculate_late_fee_for_book_incorrect_patron_id():
    # attempt to calculate return fee for a book where patron id is 5 digits long
    # it is also assumed that patron id having a corrcet form would be checked first
    # so the point of this is to check that the calculate_late_free function flags the incorrect patron_id first
    results = calculate_late_fee_for_book("22200", Book_test_id)

    assert results["fee_amount"] == 0.0
    assert results["days_overdue"] == 0
    assert "ID must be 6" in results["status"]


def test_calculate_late_fee_for_book_incorrect_patron_id_again():
    # attempt to calculate return fee for a book where patron id is 5 digits long
    # it is also assumed that patron id having a corrcet form would be checked first
    results = calculate_late_fee_for_book("3333 0", Book_test_id)

    assert results["fee_amount"] == 0.0
    assert results["days_overdue"] == 0
    assert "ID must be 6" in results["status"]




# ********************************************************************************
# ASSIGNMENT 2 ADDITIONAL TEST CASE
# ********************************************************************************
def test_calculate_late_fee_for_unavailible_book():
    # attempt to calculate return fee for a book where patron id is 5 digits long
    # it is also assumed that patron id having a corrcet form would be checked first
    add_book_to_catalog("Test Author 10", "Test Book  10", "0111111111111", 1)
    book_ten_id = get_book_by_isbn("0111111111111")["id"]
    borrow_book_by_patron("123456", book_ten_id)

    results = calculate_late_fee_for_book("223456", book_ten_id)

    assert results["fee_amount"] == 0.0
    assert results["days_overdue"] == 0
    assert "not borrowed" in results["status"].lower()

# ********************************************************************************
# ASSIGNMENT 2 END OF ADDITIONAL TEST CASES
# ********************************************************************************



# **************** Positive Test Cases ****************


def test_calculate_late_fee_for_book_immediate_return():
    # attempt to calculate return fee for when a book is immediately returned
    borrow_book_by_patron("444400", Book_test_id)
    results = calculate_late_fee_for_book("444400", Book_test_id)

    # since book was returned within the designated time frame, no issues
    assert results["fee_amount"] == 0.0
    assert results["days_overdue"] == 0
    assert "returned" in results["status"]





# next test would be manually adjusting the datetime to 14, 21, and 28 days after the inital borrowing, but I cannot do that, at least not with
# the libraries i am curently using and the current level of implementation of the test_calculate_late_fee_for_book function
