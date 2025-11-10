from services.library_service import add_book_to_catalog
import pytest

def reset_db():
    from pathlib import Path
    from database import init_database
    Path("library.db").unlink(missing_ok=True)
    init_database()

reset_db()


# **************** Negative Test Cases ****************

def test_add_book_to_catalog_zero_books():
    success, message = add_book_to_catalog("Test Book 1", "Test Author 1", "1111111111111", 0)

    assert success == False
    assert "total copies must" in message.lower()


def test_add_book_to_catalog_negative_book_number():
    success, message = add_book_to_catalog("Test Book 2", "Test Author 2", "2111111111111", -2147483649)

    assert success == False
    assert "total copies must" in message.lower()


def test_add_book_to_catalog_incorrect_isbn_len():
    # isbn13 number here is 12 digits in length, with a space character at the end
    success, message = add_book_to_catalog("Test Book 3", "Test Author 3", "311111111111 ", 5)

    assert success == False
    assert "exactly 13 digits" in message.lower()


def test_add_book_to_catalog_book_201_characters():
    # book name is exactly 201 characters long
    title = "4" * 201 
    success, message = add_book_to_catalog(title, "Test Author 4", "4111111111111", 5)

    assert success == False
    assert "200 characters" in message.lower()


def test_add_book_to_catalog_author_zero_characters():
    # author name is just spaces, so should be rejected
    success, message = add_book_to_catalog("Test Book 5", "      ", "5111111111111", 5)

    assert success == False
    assert "author is required" in message.lower()


def test_add_book_to_catalog_string_isbn():
    # isbn is a string containing characters rather than digits
    success, message = add_book_to_catalog("Test Book 6", "Test Author 6", "thirteenthree", 5)

    assert success == False
    assert "13 digits" in message.lower()



# **************** Positive Test Cases ****************

def test_add_book_to_catalog_3_billion_books():
    # try adding 3 billion books
    success, message = add_book_to_catalog("Test Book 7", "Test Author 7", "7111111111111", 3000000000)

    assert success == True
    assert "successfully added" in message.lower()


def test_add_book_to_catalog_1_book():
    # try adding 1 book
    success, message = add_book_to_catalog("Test Book 8", "Test Author 8", "8111111111111", 1)

    assert success == True
    assert "successfully added" in message.lower()


def test_add_book_to_catalog_book_200_characters():
    # book name is exactly 200 characters long
    title = "9" * 200
    success, message = add_book_to_catalog(title, "Test Author 9", "9111111111111", 5)

    assert success == True
    assert "successfully added" in message.lower()


def test_add_book_to_catalog_100_char_author_name():
    # try book with author name is 100 characters
    name = "a" * 100
    success, message = add_book_to_catalog("Test Book 10", name, "1011111111111", 5)

    assert success == True
    assert "successfully added" in message.lower()


def test_add_book_to_catalog_all_zero_isbn():
    # try adding a book where isbn is just 13 0s
    success, message = add_book_to_catalog("Test Book 11", "Test Author 11", "0000000000000", 5)

    assert success == True
    assert "successfully added" in message.lower()




# **************** Extra Negative Test Cases ****************
def test_add_book_to_catalog_existing_isbn():
    # isbn is a string containing characters rather than digits
    success, message = add_book_to_catalog("Test Book 12", "Test Author 12", "7111111111111", 5)

    assert success == False
    assert "already exists" in message.lower()