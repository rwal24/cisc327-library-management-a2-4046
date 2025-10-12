from library_service import add_book_to_catalog, borrow_book_by_patron, return_book_by_patron
from database import init_database, get_book_by_isbn
import pytest

# Note: since return_book_by_patron is not implemented, the return message will be made up here
def reset_db():
    from pathlib import Path
    Path("library.db").unlink(missing_ok=True)
    init_database()

reset_db()


init_database()
add_book_to_catalog("Book Test", "Author Test", "9087654321099", 100)

Book_test_id = get_book_by_isbn("9087654321099")["id"]


# **************** Negative Test Cases ****************

def test_return_book_by_patron_has_not_borrowed_or_dne():
    # attempt to return a book that was not borrowed
    success, message = return_book_by_patron("111110", 200)

    assert success == False
    assert "an existing book" in message.lower()


def test_return_book_by_patron_negative_id():
    # attempt to return a book with a negative book id
    success, message = return_book_by_patron("222220", -1)

    assert success == False
    assert "book id must be" in message.lower()


def test_return_book_by_char_patron_id():
    # attempt to return a where the patron id is a string of length 6
    success, message = return_book_by_patron("three3", Book_test_id)

    assert success == False
    assert "patron id must be" in message.lower()




# **************** Positive Test Cases ****************

def test_return_book_by_patron_different_return_order():
    # attempt to return books in a different order than how they were taken
    add_book_to_catalog("Book Test", "Author Test", "9087654321111", 1) 
    add_book_to_catalog("Book Test", "Author Test", "9087654322222", 1)
    add_book_to_catalog("Book Test", "Author Test", "9087654333333", 1)

    # get the actual book id for each of the books added to catalog
    Book_test_id_two = get_book_by_isbn("9087654321111")["id"]
    Book_test_id_three = get_book_by_isbn("9087654322222")["id"]
    Book_test_id_four = get_book_by_isbn("9087654333333")["id"]


    borrow_book_by_patron("333330", Book_test_id_two)
    borrow_book_by_patron("333330", Book_test_id_three)
    borrow_book_by_patron("333330", Book_test_id_four)

    return_book_by_patron("333330", Book_test_id_four)
    return_book_by_patron("333330", Book_test_id_two)
    success, message = return_book_by_patron("333330", Book_test_id_three)

    assert success == True
    assert "returned" in message.lower()
