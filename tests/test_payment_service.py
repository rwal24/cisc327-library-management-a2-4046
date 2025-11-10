from services.payment_service import PaymentGateway
import pytest

gateway = PaymentGateway()

# **************** Negative Test Cases ****************

# Testing of process_payment
def test_process_payment_amount_leq_zero():
    # test payment_process function with an amount less than the 0
    result = gateway.process_payment("123456", -1, "something")

    assert result[0] == False 
    assert result[1] == ""
    assert result[2] == "Invalid amount: must be greater than 0"



def test_process_payment_amount_g_thousand():
    # test payment_process function with an amount greater than the max possible
    result = gateway.process_payment("123456", 1001, "something")

    assert result[0] == False 
    assert result[1] == ""
    assert result[2] == "Payment declined: amount exceeds limit"



def test_process_payment_bad_usr_id():
    # test payment_process function with a bad user id
    result = gateway.process_payment("12345", 10, "something")

    assert result[0] == False 
    assert result[1] == ""
    assert result[2] == "Invalid patron ID format"


# Testing of refund_payment
def test_refund_payment_bad_transaction_id():
    # test refund_payment function with a bad transaction id
    result = gateway.refund_payment("trx_", 10)

    assert result[0] == False
    assert result[1] == "Invalid transaction ID"



def test_refund_payment_amount_leq_zero():
    # test refund_payment function with an amount leq zero
    result = gateway.refund_payment("txn_", -1)

    assert result[0] == False
    assert result[1] == "Invalid refund amount"



# Testing of verify_payment_status
def test_verify_payment_status_bad_transaction_id():
    # test verify_payment_status with a bad transcation id
    result = gateway.verify_payment_status("trx_")

    assert result["status"] == "not_found"
    assert result["message"] == "Transaction not found"
    assert len(result) == 2



# **************** Positive Test Cases ****************
# Testing of process_payment
def test_process_payment_good_inputs():
    # test payment_process function with an amount less than the 0
    result = gateway.process_payment("123456", 10, "something")

    assert result[0] == True 
    assert "txn_123456" in result[1] 
    assert result[2] == "Payment of $10.00 processed successfully"



# Testing of refund_payment
def test_refund_payment_good_inputs():
    # test refund_payment function with a bad transaction id
    result = gateway.refund_payment("txn_", 10)

    assert result[0] == True
    assert "Refund of $10.00 processed successfully." in result[1]




# Testing of verify_payment_status
def test_verify_payment_status_good_inputs():
    # test verify_payment_status with a bad transcation id
    result = gateway.verify_payment_status("txn_")

    assert result["transaction_id"] == "txn_"
    assert result["status"] == "completed"
    assert result["amount"] == 10.50
    assert len(result) == 4



