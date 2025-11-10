from services.library_service import refund_late_fee_payment, PaymentGateway
import pytest



# **************** Negative Test Cases ****************
def test_refund_incorrect_transaction_id(mocker):
    # comment boy here
    gateway = mocker.Mock(spec=PaymentGateway)

    result = refund_late_fee_payment("00102", 1, gateway)

    assert result[0] == False
    assert "Invalid transaction ID." in result[1]
    gateway.refund_payment.assert_not_called()



def test_refund_late_fee_amount_leq_zero(mocker):
    # comment or comment this
    gateway = mocker.Mock(spec=PaymentGateway)

    result = refund_late_fee_payment("txn_123", -1, gateway)

    assert result[0] == False
    assert "be greater than 0." in result[1]
    gateway.refund_payment.assert_not_called()



def test_refund_late_fee_amount_g_15(mocker):
    # other comment space (im going backwards)
    gateway = mocker.Mock(spec=PaymentGateway)

    result = refund_late_fee_payment("txn_123", 18, gateway)

    assert result[0] == False
    assert "exceeds maximum late fee." in result[1]
    gateway.refund_payment.assert_not_called()



def test_refund_late_fee_unsuccessful_refund_value(mocker):
    # comment space or something
    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = (False, "Refund of $10.00 failed to process.")

    result = refund_late_fee_payment("txn_123", 10.0, gateway)
    assert result[0] is False
    assert "Refund failed:" in result[1]
    gateway.refund_payment.assert_called_once_with("txn_123", 10.0)



# **************** Positive Test Cases ****************
def test_refund_late_fee_successful_return(mocker):
    gateway = mocker.Mock(spec=PaymentGateway)
    gateway.refund_payment.return_value = (True, "Refund of $15.00 processed successfully. Refund ID: tnx_")

    result = refund_late_fee_payment("txn_123", 15.0, gateway)
    assert result[0] == True
    assert "processed successfully." in result[1]
    gateway.refund_payment.assert_called_once_with("txn_123", 15.0)





