from services.library_service import pay_late_fees, PaymentGateway, add_book_to_catalog
from database import get_book_by_isbn
import pytest


book_id = 1


# **************** Negative Test Cases ****************
def test_pay_late_fee_incorrrect_user_id(mocker):
    # test if the pay_late_fee will accept an incorrect input
    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (True, "txn_111", "ok")

    result = pay_late_fees("11 011", book_id, gateway)
    assert result[0] == False
    assert "Invalid patron ID" in result[1]
    gateway.process_payment.assert_not_called()


def test_pay_late_fee_not_fee_info(mocker):
    # test behaviour of pay_late_fee when calculate_late_fee returns an None
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value=None,
    )
    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (True, "txn_222", "ok")

    result = pay_late_fees("123456", book_id, gateway)
    assert result[0] == False
    assert "Unable to calculate late" in result[1]
    gateway.process_payment.assert_not_called()



def test_pay_late_fee_leq_zero_owed(mocker):
    # test behaviour of pay_late_fee when calculate_late_fee returns 0 (for 0 dollars owed)
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={
            'fee_amount': 0.00,
            'days_overdue': 0,
            'status': 'Book returned before due date - no late fee applied'
        }
    )
    
    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (True, "txn_333", "ok")

    result = pay_late_fees("123456", book_id, gateway)
    assert result[0] == False
    assert "No late fees to pay" in result[1]
    gateway.process_payment.assert_not_called()




def test_pay_late_fee_incorrect_book_id(mocker):
    # test behaviour of pay_late_fee when an impossible book_id is passed as an argument
    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (True, "tnx_444", "ok")
    mocker.patch(
    "services.library_service.calculate_late_fee_for_book",
    return_value={"fee_amount": 5.0, "days_overdue": 3, "status": "late"},) # stub calculate_late_fee function

    # no book within the realm of testing will have that book_id
    result = pay_late_fees("123456", None, gateway)
    assert result[0] == False
    assert "Book not found." in result[1]
    gateway.process_payment.assert_not_called()




def test_pay_late_fee_payment_issue(mocker):
    # test behaviour of pay_late_fee when a stub for a failed payment is sent through
        # stubs so we reach the payment call
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 3.5, 
                      "days_overdue": 7, 
                      "status": "Book returned 7 days after the due date"},
    )
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 1, "title": "Test Book"},
    )

    # mock gateway: return failure
    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (False, None, "Payment Error",)

    result = pay_late_fees("123456", 1, gateway)

    assert result[0] is False
    assert "Payment failed" in result[1]

    gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=3.5,
        description="Late fees for 'Test Book'",
    )


# **************** Positive Test Cases ****************
def test_pay_late_fee_payment_goes_through(mocker):
    mocker.patch(
        "services.library_service.calculate_late_fee_for_book",
        return_value={"fee_amount": 15, 
                      "days_overdue": 18, 
                      "status": "Book returned 18 days after the due date"},
    )
    mocker.patch(
        "services.library_service.get_book_by_id",
        return_value={"id": 1, "title": "Test Book"},
    )


    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.process_payment.return_value = (True, "txn_555", "Payment of $3.5 processed successfully",)

    result = pay_late_fees("123456", 1, gateway)

    assert result[0] == True
    assert "Payment successful" in result[1]

    gateway.process_payment.assert_called_once_with(
        patron_id="123456",
        amount=15,
        description="Late fees for 'Test Book'",
    )




