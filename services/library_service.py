"""
Library Service Module - Business Logic Functions
Contains all the core business logic for the Library Management System
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database import (
    get_book_by_id, get_book_by_isbn, get_patron_borrow_count,
    insert_book, insert_borrow_record, update_book_availability,
    update_borrow_record_return_date, get_all_books, get_patron_borrowed_books
)
from .payment_service import PaymentGateway



def add_book_to_catalog(title: str, author: str, isbn: str, total_copies: int) -> Tuple[bool, str]:
    """
    Add a new book to the catalog.
    Implements R1: Book Catalog Management
    
    Args:
        title: Book title (max 200 chars)
        author: Book author (max 100 chars)
        isbn: 13-digit ISBN
        total_copies: Number of copies (positive integer)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Input validation
    if not title or not title.strip():
        return False, "Title is required."
    
    if len(title.strip()) > 200:
        return False, "Title must be less than 200 characters."
    
    if not author or not author.strip():
        return False, "Author is required."
    
    if len(author.strip()) > 100:
        return False, "Author must be less than 100 characters."
    
    # Fixed error which allowed incorrect isbn numbers to be passed
    isbn = isbn.replace(" ", "")
    if not isbn.isdigit() or len(isbn) != 13:
        return False, "ISBN must be exactly 13 digits."
    
    if not isinstance(total_copies, int) or total_copies <= 0:
        return False, "Total copies must be a positive integer."
    
    # Check for duplicate ISBN
    existing = get_book_by_isbn(isbn)
    if existing:
        return False, "A book with this ISBN already exists."
    
    # Insert new book
    success = insert_book(title.strip(), author.strip(), isbn, total_copies, total_copies)
    if success:
        return True, f'Book "{title.strip()}" has been successfully added to the catalog.'
    else:
        return False, "Database error occurred while adding the book."



def borrow_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Allow a patron to borrow a book.
    Implements R3 as per requirements  
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book to borrow
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found."
    
    if book['available_copies'] <= 0:
        return False, "This book is currently not available."
    
    # Check patron's current borrowed books count
    current_borrowed = get_patron_borrow_count(patron_id)
    
    # Fixed error which allowed 6 books to be borrowed
    if current_borrowed >= 5:
        return False, "You have reached the maximum borrowing limit of 5 books."
    
    # Create borrow record
    borrow_date = datetime.now()
    due_date = borrow_date + timedelta(days=14)
    
    # Insert borrow record and update availability
    borrow_success = insert_borrow_record(patron_id, book_id, borrow_date, due_date)
    if not borrow_success:
        return False, "Database error occurred while creating borrow record."
    
    availability_success = update_book_availability(book_id, -1)
    if not availability_success:
        return False, "Database error occurred while updating book availability."
    
    return True, f'Successfully borrowed "{book["title"]}". Due date: {due_date.strftime("%Y-%m-%d")}.'



def return_book_by_patron(patron_id: str, book_id: int) -> Tuple[bool, str]:
    """
    Process book return by a patron.
    
    TODO: Implement R4 as per requirements
    """
    # Lines reusede from borrow book function
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Patron id must be exactly 6 digits."
    
    # Check if book exists and is available
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book Id Must be an existing book"

    # Check if book was borrowed by the user in question
    book_found = False
    borrowed_books = get_patron_borrowed_books(patron_id)
    for book in borrowed_books:
        if book["book_id"] == book_id:
            book_found = True
            break

    if not book_found:
        return False, "Book was not borrowed by this user"
    

    # If all previous checks are valid, update user borrowed books, calculate the late fee
    # and update the availibility of the book itself


    late_fee = calculate_late_fee_for_book(patron_id, book_id)
    if late_fee:
        return True, f"Fee Amount: {late_fee['fee_amount']}.  Days Overdue: {late_fee['days_overdue']}.  Status: {late_fee['status']}"
    

    if not update_borrow_record_return_date(patron_id, book_id, datetime.now()):
        return False, "Updating borrow record failed"
    
    if not update_book_availability(book_id, 1):
        return False, "Updating book availability failed"
    
    return False, "Unidentified error"

    

    


def calculate_late_fee_for_book(patron_id: str, book_id: int) -> Dict:
    """
    Calculate late fees for a specific book.
    
    TODO: Implement R5 as per requirements 
    
    
    return { // return the calculated values
        'fee_amount': 0.00,
        'days_overdue': 0,
        'status': 'Late fee calculation not implemented'
    }
    """

    # Lines reusede from borrow book function
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return  {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Patron ID must be 6 digits'
        }
    
    # Check if book exists and is available
    bk = get_book_by_id(book_id)
    if not bk:
        return  {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book does not exist or is not available'
        }

    # check again if user borrowed the book in question (already checked in return book function)
    this_book = None
    borrowed_books = get_patron_borrowed_books(patron_id)
    for book in borrowed_books:
        if book["book_id"] == book_id:
            this_book = book
            break

    if not this_book:
        return  {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book not borrowed by this user'
        }
    

    time_now = datetime.now().date()
    time_due = this_book["due_date"].date()

    if not this_book["is_overdue"]:
        return  {
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book returned before due date - no late fee applied'
        }
    
    else:
        # calculate late fee, return result in json format
        days_overdue = (time_now - time_due).days

        # 0.5 dollar sper day up to 7 days
        if days_overdue <= 7:
            return  {
                'fee_amount': days_overdue * 0.5,
                'days_overdue': days_overdue,
                'status': f'Book returned {days_overdue} days after the due date'
            }
        
        # 1 dollar per day after 7 days, up to 18 days (ater 18, fine stays at $15)
        elif 7 < days_overdue <= 18:
            return  {
                'fee_amount': 3.5 + (days_overdue - 7),
                'days_overdue': days_overdue,
                'status': f'Book returned {days_overdue} days after the due date'
            }
        
        else:
            return  {
                'fee_amount': 15.00,
                'days_overdue': days_overdue,
                'status': f'Book returned {days_overdue} days after the due date'
            }


            






def search_books_in_catalog(search_term: str, search_type: str) -> List[Dict]:
    """
    Search for books in the catalog.
    
    TODO: Implement R6 as per requirements
    """
    
    # return empty list if search_term or search_type are anything but strings
    if not isinstance(search_term, str) or not isinstance(search_type, str):
        return []
    
    search_type = search_type.lower()
    # if an incorrect search type is input, return empty list
    if search_type not in ["author", "title", "isbn"]:
        return []
    
    all_books = get_all_books()
    
    results = []

    # if search term is empty string, then the search will always return nothing, no matter the search type
    if search_term == "":
        return results


    # search by author
    if search_type == "author":
        q = search_term.lower()
        for book in all_books:
            if q in book["author"].lower():
                results.append(book)
        return results

    # search by title
    if search_type == "title":
        q = search_term.lower()
        for book in all_books:
            if q in book["title"].lower() or q == book["title"].lower():
                results.append(book)
        return results 
    
    # search by isbn
    if search_type == "isbn":
        q = search_term
        # check that q is a valid isbn number
        if not q.isdigit() or len(q) != 13:
            return []
        
        for book in all_books:
            # isbn is digits, and therefor cannot be in loewrcase. other code ensures isbn is correct
            if q == book["isbn"]:
                results.append(book)
        return results 
    
    # in case of some unidentified error
    return []



def get_patron_status_report(patron_id: str) -> Dict:
    """
    Get status report for a patron.
    
    TODO: Implement R7 as per requirements
    """

    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return {}
    
    report = {
        "patron_id": patron_id,
        "currently_borrowed": [],
        "owed_late_fees": 0.00,
        "current_borrow_count": 0,
        "borrow_history": [],
        "status": "No issues"
    }
    borrow_count = get_patron_borrow_count(patron_id)

    if borrow_count == 0:
        return report

    borrowed_books = get_patron_borrowed_books(patron_id)
    total_fee = 0.00

    # handle calculations of total late fees, as well as creating a list of tuples for borrowed books and their due dates
    for book in borrowed_books:
        fee_info = calculate_late_fee_for_book(patron_id, book["book_id"])
        report["currently_borrowed"].append((book["title"], book["due_date"]))
        total_fee += fee_info["fee_amount"]
    
    report["owed_late_fees"] = total_fee
    report["current_borrow_count"] = borrow_count

    return report




# CODE FOR PART 1
def pay_late_fees(patron_id: str, book_id: int, payment_gateway: PaymentGateway = None) -> Tuple[bool, str, Optional[str]]:
    """
    Process payment for late fees using external payment gateway.
    
    NEW FEATURE FOR ASSIGNMENT 3: Demonstrates need for mocking/stubbing
    This function depends on an external payment service that should be mocked in tests.
    
    Args:
        patron_id: 6-digit library card ID
        book_id: ID of the book with late fees
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str, transaction_id: Optional[str])
        
    Example for you to mock:
        # In tests, mock the payment gateway:
        mock_gateway = Mock(spec=PaymentGateway)
        mock_gateway.process_payment.return_value = (True, "txn_123", "Success")
        success, msg, txn = pay_late_fees("123456", 1, mock_gateway)
    """
    # Validate patron ID
    if not patron_id or not patron_id.isdigit() or len(patron_id) != 6:
        return False, "Invalid patron ID. Must be exactly 6 digits.", None
    
    # Calculate late fee first
    fee_info = calculate_late_fee_for_book(patron_id, book_id)
    
    # Check if there's a fee to pay
    if not fee_info or 'fee_amount' not in fee_info:
        return False, "Unable to calculate late fees.", None
    
    fee_amount = fee_info.get('fee_amount', 0.0)
    
    if fee_amount <= 0:
        return False, "No late fees to pay for this book.", None
    
    # Get book details for payment description
    book = get_book_by_id(book_id)
    if not book:
        return False, "Book not found.", None
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process payment through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN THEIR TESTS!
    try:
        success, transaction_id, message = payment_gateway.process_payment(
            patron_id=patron_id,
            amount=fee_amount,
            description=f"Late fees for '{book['title']}'"
        )
        
        if success:
            return True, f"Payment successful! {message}", transaction_id
        else:
            return False, f"Payment failed: {message}", None
            
    except Exception as e:
        # Handle payment gateway errors
        return False, f"Payment processing error: {str(e)}", None







def refund_late_fee_payment(transaction_id: str, amount: float, payment_gateway: PaymentGateway = None) -> Tuple[bool, str]:
    """
    Refund a late fee payment (e.g., if book was returned on time but fees were charged in error).
    
    NEW FEATURE FOR ASSIGNMENT 3: Another function requiring mocking
    
    Args:
        transaction_id: Original transaction ID to refund
        amount: Amount to refund
        payment_gateway: Payment gateway instance (injectable for testing)
        
    Returns:
        tuple: (success: bool, message: str)
    """
    # Validate inputs
    if not transaction_id or not transaction_id.startswith("txn_"):
        return False, "Invalid transaction ID."
    
    if amount <= 0:
        return False, "Refund amount must be greater than 0."
    
    if amount > 15.00:  # Maximum late fee per book
        return False, "Refund amount exceeds maximum late fee."
    
    # Use provided gateway or create new one
    if payment_gateway is None:
        payment_gateway = PaymentGateway()
    
    # Process refund through external gateway
    # THIS IS WHAT YOU SHOULD MOCK IN YOUR TESTS!
    try:
        success, message = payment_gateway.refund_payment(transaction_id, amount)
        
        if success:
            return True, message
        else:
            return False, f"Refund failed: {message}"
            
    except Exception as e:
        return False, f"Refund processing error: {str(e)}"