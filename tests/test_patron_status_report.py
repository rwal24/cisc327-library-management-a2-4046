from library_service import get_patron_status_report, add_book_to_catalog, return_book_by_patron, borrow_book_by_patron
from database import init_database, get_book_by_isbn
import pytest

def reset_db():
    from pathlib import Path
    Path("library.db").unlink(missing_ok=True)
    init_database()

reset_db()
add_book_to_catalog("Book Tester", "Author Tester", "9087654321099", 100)
Book_test_id = get_book_by_isbn("9087654321099")["id"]

add_book_to_catalog("Book Tester 2", "Author Tester 2", "2087654321099", 100)
Book_test_id_two = get_book_by_isbn("2087654321099")["id"]

add_book_to_catalog("Book Tester 3", "Author Tester 3", "3087654321099", 100)
Book_test_id_three = get_book_by_isbn("3087654321099")["id"]

# A quick assumption will be made that all values in the returned dictionary of the get_patron_status_report 
# function will all be strings besides the total overdue amount


# **************** Negative Test Cases ****************
def test_get_patron_status_report_non_existent_patron():
    # should return empty dictionary since patron DNE
    borrow_book_by_patron("111111", Book_test_id)
    result_dict = get_patron_status_report("111110")
    assert isinstance(result_dict, dict)
    assert result_dict["patron_id"] == "111110"
    assert result_dict["currently_borrowed"] == []
    assert result_dict["owed_late_fees"] == 0.0
    assert result_dict["current_borrow_count"] == 0



def test_get_patron_status_report_incorrect_patron_id():
    # should return empty dictionary since patron is incorrect format
    borrow_book_by_patron("222222", Book_test_id)
    result_dict = get_patron_status_report("222 22") # id is 5 charcaters long rather than 1 here
    assert len(result_dict) == 0

# not much negative case testing is possible since the function only takes one arguement


# **************** Positive Test Cases ****************
def test_get_patron_status_report_show_all_borrowed_books():
    # should return a dictionary where only currently borrowed books are displayed with zero late return fee
    borrow_book_by_patron("333333", Book_test_id)
    borrow_book_by_patron("333333", Book_test_id_two)
    borrow_book_by_patron("333333", Book_test_id_three)
    result_dict = get_patron_status_report("333333")

    assert len(result_dict["currently_borrowed"]) == 3
    assert result_dict["owed_late_fees"] == 0.0
    assert result_dict["current_borrow_count"] == 3


def test_get_patron_status_report_show_all_returned_books():
    # should return a dictionary where there is 1 currently borrowed books, 2 in borrow history, and zero owed
    borrow_book_by_patron("444444", Book_test_id)
    borrow_book_by_patron("444444", Book_test_id_two)
    borrow_book_by_patron("444444", Book_test_id_three)

    return_book_by_patron("444444", Book_test_id)
    return_book_by_patron("444444", Book_test_id_two)
    result_dict = get_patron_status_report("444444")


    assert len(result_dict["currently_borrowed"]) == 1
    assert result_dict["owed_late_fees"] == 0
    assert len(result_dict["borrow_history"]) == 2



