import re
import random
from playwright.sync_api import Page, expect

def generate_unique_isbn() -> str:
    # 13-digit "ISBN":
    # start with a non-zero digit, then 12 random digits
    return "9" + "".join(str(random.randint(0, 9)) for _ in range(12))


isbn1 = generate_unique_isbn()
isbn2 = generate_unique_isbn()

title1 = "Test Book e2e 1" + isbn1
title2 = "Test Book e2e 2" + isbn2




# test for: add new book to catalog -> borrow said book -> verify book was borrowed
def test_cycle_1_e2e(page: Page):
    page.goto("http://localhost:5001/catalog")          # go to the catalog page for the website

    # create a new locator for the page when you click "add book to catalog"
    page.get_by_role("link", name=re.compile("Add New Book")).click()
    # this is effectively the link "http://localhost:5000/add_book"

    # ill in the boxes to add a new book to the catalog of books. use the ID from add_book.html
    page.fill("#title", title1)
    page.fill("#author", "Test Author e2e 1")
    page.fill("#isbn", isbn1)
    page.fill("#total_copies", "3")

    # submit the form to add a new book to the catalog by "pressing" the "Add Book to Catalog" button found in add_book.html
    page.get_by_role("button", name=re.compile("Add.*book", re.IGNORECASE)).click()
    # submitting the "add new book" form takes us back to catalog.html


    # this would be the assert for ii) in the example
    expect(page.get_by_role("row", name=re.compile(title1))).to_be_visible()

    # next step would be navigating to the borrow book page, however, book is borrowed directly from the catalog page, so no movement required

    row = page.get_by_role("row", name=re.compile(title1))
    row.locator('input[name="patron_id"]').fill("123456")
    row.get_by_role("button", name="Borrow").click()
    book_id = row.locator('input[name="book_id"]').input_value()

    expect(page.locator("body")).to_contain_text(f"Successfully borrowed \"{title1}\".")

    # navigate to book return and fill out page
    page.get_by_role("link", name=re.compile("Return Book")).click()
    page.fill("#book_id", book_id)
    page.fill("#patron_id", "123456")

    # return book for repeatability
    page.get_by_role("button", name="Process Return").click()


    
# Second e2e function. the execution flow will be as follows:
# catalog -> add_new_book with 1 copy -> borrow book (assert) -> borrow book (cannot, unavailable) ->
# -> return book (original id - assert book count = 1  -> borrow book (different user id)
def test_cycle_2_e2e(page: Page):
    page.goto("http://localhost:5001/catalog")          # go to the catalog page for the website

    # create a new locator for the page when you click "add book to catalog"
    page.get_by_role("link", name=re.compile("Add New Book")).click()
    # this is effectively the link "http://localhost:5000/add_book"

    # ill in the boxes to add a new book to the catalog of books. use the ID from add_book.html
    page.fill("#title", title2)
    page.fill("#author", "Test Author e2e 2")
    page.fill("#isbn", isbn2)
    page.fill("#total_copies", "1")

    # submit the form to add a new book to the catalog by "pressing" the "Add Book to Catalog" button found in add_book.html
    page.get_by_role("button", name=re.compile("Add.*book", re.IGNORECASE)).click()
    # submitting the "add new book" form takes us back to catalog.html


    # this would be the assert for ii) in the example
    expect(page.get_by_role("row", name=re.compile(title2))).to_be_visible()

    # next step would be navigating to the borrow book page, however, book is borrowed directly from the catalog page, so no movement required

    row = page.get_by_role("row", name=re.compile(title2))
    expect(row).to_be_visible()

    # expect only 1 book available
    expect(row).to_contain_text("1/1 Available")

    # get the book id to be used in the return
    book_id = row.locator('input[name="book_id"]').input_value()

    # borrow book for user 1 (user id 111111)
    row.locator('input[name="patron_id"]').fill("111111")
    row.get_by_role("button", name="Borrow").click()


    # expect a successful message of borrowing
    expect(page.locator("body")).to_contain_text(f"Successfully borrowed \"{title2}\".")

    # expect a message which now states that no books are available here
    expect(row).to_contain_text("Not Available")


    # navigate to book return and fill out page
    page.get_by_role("link", name=re.compile("Return Book")).click()
    page.fill("#book_id", book_id)
    page.fill("#patron_id", "111111")

    # return book
    page.get_by_role("button", name="Process Return").click()
    expect(page.locator("body")).to_contain_text("Fee Amount: 0.0. Days Overdue: 0. Status: Book returned before due date - no late fee applied")
    # expect no fee since it was returned immediately


    # head back to the catalog
    page.get_by_role("link", name=re.compile("Catalog")).click()

    # expect to find 1/1 Available next to the newly returned book
    row = page.get_by_role("row", name=re.compile(title2))
    expect(row).to_contain_text("1/1 Available")

    # fill out the patron id, borrow the returned book
    row.locator('input[name="patron_id"]').fill("222222")
    row.get_by_role("button", name="Borrow").click()

    #expect a successful message of borrowing
    expect(page.locator("body")).to_contain_text(f"Successfully borrowed \"{title2}\".")


    # navigate to book return and fill out page
    page.get_by_role("link", name=re.compile("Return Book")).click()
    page.fill("#book_id", book_id)
    page.fill("#patron_id", "222222")

    # return book for repeatability
    page.get_by_role("button", name="Process Return").click()



# Third e2e function. the execution flow will be as follows:
# catalog -> search_book -> search book by isbn (select option and fill out isbn number) -> presss search
# verify book exists and is available -> catalog -> borrow book
def test_cycle_3_e2e(page: Page):
    page.goto("http://localhost:5001/catalog")          # go to the catalog page for the website

    # create a new locator for the page when you click "Search"
    page.get_by_role("link", name=re.compile("Search", re.IGNORECASE)).click()

    # make sure we are in the correct area
    expect(page.get_by_role("heading", name="🔍 Search Books")).to_be_visible()

    # select the option to search by isbn
    page.locator("#type").select_option("isbn")

    # fill in the slot with the isbn number
    page.fill("#q", isbn2)

    # click the search button
    page.get_by_role("button", name=re.compile("Search", re.IGNORECASE)).click()

    # get the row for the book
    row = page.get_by_role("row", name=re.compile(title2))
    expect(row).to_be_visible()
    expect(row).to_contain_text("Available")

    # head back to main catalog page
    page.get_by_role("link", name="View All Books").click()

    # get the row which the page we search for is on and expect it to be visible
    row = page.get_by_role("row", name=re.compile(title2))
    expect(row).to_be_visible()
    book_id = row.locator('input[name="book_id"]').input_value()

    # borrow book for user 1 (user id 333333)
    row.locator('input[name="patron_id"]').fill("333333")
    row.get_by_role("button", name="Borrow").click()
    

    # expct that the borrow was successful
    expect(page.locator("body")).to_contain_text(f'Successfully borrowed "{title2}".')

    # navigate to book return and fill out page
    page.get_by_role("link", name=re.compile("Return Book")).click()
    page.fill("#book_id", book_id)
    page.fill("#patron_id", "333333")

    # return book for repeatability
    page.get_by_role("button", name="Process Return").click()



    