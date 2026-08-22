from apps.loans.models import Loan, LoanPayment


def get_customer_loans(
    customer_id,
    status=None,
):
    loans = (
        Loan.objects
        .filter(
            customer_id=customer_id
        )
    )

    if status:

        loans = loans.filter(
            status=status.upper()
        )

    loans = (
        loans
        .order_by("-created_at")
        .values(
            "id",
            "loan_type",
            "outstanding_amount",
            "monthly_emi",
            "tenure_years",
            "interest_rate",
            "status",
            "next_due_date",
        )
    )

    return {
        "customer_id": str(customer_id),
        "count": loans.count(),
        "loans": list(loans),
    }


def get_loan_payment_history(
    customer_id,
    loan_id=None,
    start_date=None,
    end_date=None,
):
    payments = (
        LoanPayment.objects
        .select_related("loan")
        .filter(
            loan_id=loan_id,
            loan__customer_id=customer_id,
        )
    )

    if start_date:

        payments = payments.filter(
            payment_date__date__gte=start_date
        )

    if end_date:

        payments = payments.filter(
            payment_date__date__lte=end_date
        )

    payments = (
        payments
        .order_by("-payment_date")
        .values(
            "payment_number",
            "amount",
            "payment_date",
        )
    )

    return {
        "customer_id": str(customer_id),
        "loan_id": str(loan_id),
        "count": payments.count(),
        "payments": list(payments),
    }