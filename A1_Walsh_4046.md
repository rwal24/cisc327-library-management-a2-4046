Name: Ryan Walsh
Student ID: 20414046
Group Number: 4



|          Function Name           | Implementation Status | What is Missing            |
|----------------------------------|-----------------------|----------------------------|
| add_book_to_catalog (R1)         | Complete              | Nothing                    |
| borrow_book_by_patron (R3)       | Complete              | Nothing                    |
| create_app (display) (R2)        | Complete              | Nothing (UI only)          |
| return_book_by_patron (R4)       | Incomplete            | No Implementation provided |
| calculate_late_fee_for_book (R5) | Incomplete            | No Implementation provided |
| search_books_in_catalog (R6)     | Incomplete            | No Implementation provided |
| get_patron_status_report (R7)    | Incomplete            | No Implementation provided |

Note:
All Incomplete functions do return the correct types in the form of stand in/basic return values, 
except for the function "calculate_late_fee_for_book" (R5), which has no return value in its current state.


PART 3 OBSERVATIONS/FINDINGS:
1. The add_book_to_catalog function only checks if the isbn string argument is of length 13 - not if the string itself is valid. 
First example, the function rejects the string "311111111111 ". The overall string length is 14, however without whitespaces, it is 13, and a valid isbn argument at that. This string should therefor be rejected, not accepted. 

Second example is when the isbn argument "thirteenthree" is accepted. This is clearly NOT an isbn number, but since it is of length 13, the function still accepts it as an argument.

(TLDR: code only checks if len(isbn) == 13, not if isbn is an actual acceptable isbn number)

2. The book_borrow_by_patron function also as a flaw which allows a user to borrow 6 books. The issue here is that the function checks if a user has borrowed more than 5 books, and rejects if the user has borrowed more than 5 books, and because of this, if a user is on their fifth borrowed book, the function allows them to borrow a sixth. This is against the requirements of this function, which states that a single patron can borrow "max 5 books"



PART 3 TEST SUMMARY:
- test_add_book.py — R1, tests: title/author string length follows R1, ISBN length == 13 - does not check string content, duplicates covered, copies added must be > 0 as per R1.
- test_borrow_book.py — R3, tests: patron ID follows R3 format, availability is always checked, borrow-limits incorrect (allows 6th borrow), bad book_id is rejected.
- test_book_return.py — R4, tests: unimplemented, test returning non-borrowed, patron id < 0, non-numeric patron id, different return order.
- test_late_fee.py — R5, tests: unimplemented, fee for non-borrowed book, incorrect book id & patron id, return fee for immediate return.
- test_book_search.py — R6, tests: unimplemented, non-existent isbn, len(isbn) !=13, empty author & string argument, author & title string matching and case sensitivity, isbn correctness.
- test_patron_status_report.py — R7, tests: unimplemented, report non-existent patron, incorrect patron id, books borrowed, books returned


Since no other functions are implemented in library_services.py, this is the extent of the observations. Furthermore, no testing is really possible for R2 (create_app/display) because this is a flask frontend program which takes no arguments - the only testing that is really possible is testing the functionality of the website itself.

All other function tests also fail because they are unit testing scripts for unimplemented features. They do take some liberties in assuming what a reasonable output may also look like too

