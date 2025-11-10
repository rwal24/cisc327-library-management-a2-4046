from services.library_service import borrow_book_by_patron, add_book_to_catalog
from database import init_database, get_book_by_isbn
import pytest


def reset_db():
    from pathlib import Path
    Path("library.db").unlink(missing_ok=True)
    init_database()

# reset database for every test
reset_db()


add_book_to_catalog("Book Test", "Author Test", "9087654321099", 100)

Book_test_id = get_book_by_isbn("9087654321099")["id"]


# **************** Negative Test Cases ****************
def test_borrow_book_by_patron_random_book_id():
    # try borrowing a book with an incorrect isbn length
    success, message = borrow_book_by_patron("111111", 20)

    assert success == False
    assert "not found" in message.lower()


def test_borrow_book_by_patron_borrow_6_books():
    # try borrowing 6 books without returning any
    borrow_book_by_patron("211111", Book_test_id)
    borrow_book_by_patron("211111", Book_test_id)
    borrow_book_by_patron("211111", Book_test_id)
    borrow_book_by_patron("211111", Book_test_id)
    borrow_book_by_patron("211111", Book_test_id)
    success, message = borrow_book_by_patron("211111", Book_test_id)

    assert success == False
    assert "maximum borrowing limit" in message.lower()


def test_borrow_book_by_patron_incorrect_patron_id():
    # try borrowing a book with an incorrect patron id
    success, message = borrow_book_by_patron("311 11", Book_test_id)

    assert success == False
    assert "invalid patron" in message.lower()


def test_borrow_book_by_patron_incorrect_patron_id_again():
    # try borrowing a book with an incorrect patron id
    success, message = borrow_book_by_patron("41111 ", Book_test_id)

    assert success == False
    assert "invalid patron" in message.lower()


def test_borrow_book_by_patron_out_of_stock_book():
    # try borrowing a book thats out of stock
    add_book_to_catalog("Book Test 2", "Author Test 2", "2222222222222", 1)
    Book_test_id_two = get_book_by_isbn("2222222222222")["id"]

    borrow_book_by_patron("511111", Book_test_id_two)
    success, message = borrow_book_by_patron("511111", Book_test_id_two)

    assert success == False
    assert "not available" in message.lower()




# **************** Positive Test Cases ****************

def test_borrow_book_by_patron_5_books():
    # try borrowing exactly 5 books
    borrow_book_by_patron("611111", Book_test_id)
    borrow_book_by_patron("611111", Book_test_id)
    borrow_book_by_patron("611111", Book_test_id)
    borrow_book_by_patron("611111", Book_test_id)
    success, message = borrow_book_by_patron("611111", Book_test_id)


    assert success == True
    assert "successfully borrowed" in message.lower()



def test_borrow_book_by_patron_last_book():
    # try borrowing the last book remaining of a specific isbn
    add_book_to_catalog("Book Test 3", "Author Test 3", "3333333333333", 1)
    Book_test_id_three = get_book_by_isbn("9087654321099")["id"]

    success, message = borrow_book_by_patron("711111", Book_test_id_three)

    assert success == True
    assert "successfully borrowed" in message.lower()

