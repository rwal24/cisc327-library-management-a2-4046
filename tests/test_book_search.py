from library_service import search_books_in_catalog, add_book_to_catalog
from database import init_database, get_book_by_isbn
import pytest
from pathlib import Path


# to ensure the test code does not fail
def setup_function(_):
    # fresh DB
    Path("library.db").unlink(missing_ok=True)
    init_database()

    # seed exactly what these tests expect
    add_book_to_catalog("Book Tester",  "Author Tester",  "9087654321099", 100)
    add_book_to_catalog("Book Tester 2","Author Tester 2","8087654321099", 100)
    add_book_to_catalog("Book Tester 3","Author Tester 3","7087654321099", 100)
    add_book_to_catalog("Book Tester 4","Author Tester 4","6087654321099", 100)


add_book_to_catalog("Book Tester", "Author Tester", "9087654321099", 100)
Book_test_id = get_book_by_isbn("9087654321099")["id"]

add_book_to_catalog("Book Tester 2", "Author Tester 2", "8087654321099", 100)
Book_test_id_two = get_book_by_isbn("8087654321099")["id"]

add_book_to_catalog("Book Tester 3", "Author Tester 3", "7087654321099", 100)
Book_test_id_three = get_book_by_isbn("7087654321099")["id"]

add_book_to_catalog("Book Tester 4", "Author Tester 4", "6087654321099", 100)
Book_test_id_four = get_book_by_isbn("6087654321099")["id"]


# **************** Negative Test Cases ****************
def test_search_books_in_catalog_no_isbn():
    # isbn must be exact, make sure it fails on search, this one should return an empty list
    result_list = search_books_in_catalog("9087654321000", "isbn")
    assert len(result_list) == 0


def test_search_books_in_catalog_incorrect_isbn_length():
    # isbn must be exactly a set character length, make sure it fails on search, this one should return an empty list
    result_list = search_books_in_catalog("90876543210999", "isbn")
    assert len(result_list) == 0


def test_search_books_in_catalog_no_author():
    # search author name based on empty string, should return nothing
    result_list = search_books_in_catalog("", "author")
    assert len(result_list) == 0


def test_search_books_in_catalog_no_book_title():
    # search book title based on empty string, should return nothing
    result_list = search_books_in_catalog("", "title")
    assert len(result_list) == 0



# **************** Positive Test Cases ****************
def test_search_books_in_catalog_book_name_match_test_title():
    # should return all 4 books added to the data base since by title and author, substring matching is present
    # this test is for the title
    result_list = search_books_in_catalog("Book Tester", "title")
    assert len(result_list) == 4


def test_search_books_in_catalog_book_name_match_test_author():
    # should return all 4 books added to the data base since by title and author, substring matching is present
    # this test is for the title
    result_list = search_books_in_catalog("Author Tester", "author")
    assert len(result_list) == 4


def test_search_books_in_catalog_case_sensitivity_author():
    # it is case insensitive for both book title nad author. this is to test the author
    result_list = search_books_in_catalog("auTHoR tEsTer 2", "author")
    assert len(result_list) == 1 
    assert result_list[0]["author"].lower() == "author tester 2"


def test_search_books_in_catalog_case_sensitivity_title():
    # it is case insensitive for both book title nad author. this is to test the author
    result_list = search_books_in_catalog("BOOk tESTER 4", "title")
    assert len(result_list) == 1 
    assert result_list[0]["title"].lower() == "book tester 4"


def test_search_books_in_catalog_case_test_isbn_working():
    # it is case insensitive for both book title nad author. this is to test the author
    result_list = search_books_in_catalog("9087654321099", "isbn") # Book Tester 1 for this
    assert len(result_list) == 1 
    assert str(result_list[0]["isbn"]) == "9087654321099"
