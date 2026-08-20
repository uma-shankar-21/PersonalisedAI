from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from apps.loans.models import Loan, LoanPayment


class Command(BaseCommand):

    help = (
        "Final validation for loans and loan payments. "
        "This command does NOT modify any data."
    )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("=" * 100)
        self.stdout.write("FINAL LOAN DATA VALIDATION")
        self.stdout.write("=" * 100)

        now = timezone.now()

        loans = Loan.objects.all()

        total_loans = loans.count()
        total_payments = LoanPayment.objects.count()

        invalid_emi = 0
        invalid_outstanding = 0
        invalid_principal = 0
        invalid_dates = 0
        invalid_payment_dates = 0
        invalid_payment_amounts = 0
        invalid_payment_sequences = 0
        excess_payments = 0
        future_payments = 0

        self.stdout.write("")
        self.stdout.write(f"Total loans: {total_loans}")
        self.stdout.write(f"Total loan payments: {total_payments}")

        self.stdout.write("")
        self.stdout.write("-" * 100)
        self.stdout.write("VALIDATING LOANS")
        self.stdout.write("-" * 100)

        for loan in loans.iterator(chunk_size=500):

            total_months = loan.tenure_years * 12

            expected_emi = self.calculate_simple_interest_emi(
                principal=loan.principal_amount,
                interest_rate=loan.interest_rate,
                tenure_years=loan.tenure_years,
            )

            if loan.monthly_emi != expected_emi:

                invalid_emi += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nINVALID EMI"
                        f"\nLoan ID: {loan.id}"
                        f"\nStored EMI: {loan.monthly_emi}"
                        f"\nExpected EMI: {expected_emi}"
                    )
                )

            if loan.principal_amount <= Decimal("0"):

                invalid_principal += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nINVALID PRINCIPAL"
                        f"\nLoan ID: {loan.id}"
                        f"\nPrincipal: {loan.principal_amount}"
                    )
                )

            if loan.outstanding_amount < Decimal("0"):

                invalid_outstanding += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nNEGATIVE OUTSTANDING AMOUNT"
                        f"\nLoan ID: {loan.id}"
                        f"\nOutstanding: {loan.outstanding_amount}"
                    )
                )

            maximum_payable = (
                loan.monthly_emi
                * total_months
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )

            if loan.outstanding_amount > maximum_payable:

                invalid_outstanding += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nINVALID OUTSTANDING AMOUNT"
                        f"\nLoan ID: {loan.id}"
                        f"\nOutstanding: {loan.outstanding_amount}"
                        f"\nMaximum payable: {maximum_payable}"
                    )
                )

            if loan.created_at > now:

                invalid_dates += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nFUTURE LOAN START DATE"
                        f"\nLoan ID: {loan.id}"
                        f"\nCreated At: {loan.created_at}"
                    )
                )

            if (
                loan.next_due_date
                and loan.next_due_date < loan.created_at.date()
            ):

                invalid_dates += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nINVALID NEXT DUE DATE"
                        f"\nLoan ID: {loan.id}"
                        f"\nLoan Start: {loan.created_at.date()}"
                        f"\nNext Due Date: {loan.next_due_date}"
                    )
                )

        self.stdout.write("")
        self.stdout.write("-" * 100)
        self.stdout.write("VALIDATING LOAN PAYMENTS")
        self.stdout.write("-" * 100)

        loans_with_payment_counts = (
            Loan.objects
            .annotate(
                payment_count=Count("payments")
            )
            .order_by("id")
        )

        for loan in loans_with_payment_counts.iterator(
            chunk_size=500
        ):

            payments = (
                LoanPayment.objects
                .filter(loan=loan)
                .order_by(
                    "payment_number",
                    "payment_date",
                )
            )

            expected_payment_number = 1
            total_months = loan.tenure_years * 12

            for payment in payments.iterator(chunk_size=500):

                if payment.payment_date < loan.created_at:

                    invalid_payment_dates += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nPAYMENT BEFORE LOAN START"
                            f"\nLoan ID: {loan.id}"
                            f"\nPayment ID: {payment.id}"
                            f"\nLoan Start: {loan.created_at}"
                            f"\nPayment Date: {payment.payment_date}"
                        )
                    )

                if payment.payment_date > now:

                    future_payments += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nFUTURE PAYMENT"
                            f"\nLoan ID: {loan.id}"
                            f"\nPayment ID: {payment.id}"
                            f"\nPayment Date: {payment.payment_date}"
                        )
                    )

                if payment.amount != loan.monthly_emi:

                    invalid_payment_amounts += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nWRONG PAYMENT AMOUNT"
                            f"\nLoan ID: {loan.id}"
                            f"\nPayment Number: {payment.payment_number}"
                            f"\nStored Amount: {payment.amount}"
                            f"\nExpected EMI: {loan.monthly_emi}"
                        )
                    )

                if (
                    payment.payment_number
                    != expected_payment_number
                ):

                    invalid_payment_sequences += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f"\nINVALID PAYMENT SEQUENCE"
                            f"\nLoan ID: {loan.id}"
                            f"\nExpected Payment Number: "
                            f"{expected_payment_number}"
                            f"\nActual Payment Number: "
                            f"{payment.payment_number}"
                        )
                    )

                    expected_payment_number = (
                        payment.payment_number + 1
                    )

                else:

                    expected_payment_number += 1

            if loan.payment_count > total_months:

                excess_payments += 1

                self.stdout.write(
                    self.style.ERROR(
                        f"\nEXCESS PAYMENTS"
                        f"\nLoan ID: {loan.id}"
                        f"\nTenure Months: {total_months}"
                        f"\nPayment Records: "
                        f"{loan.payment_count}"
                    )
                )

        total_errors = (
            invalid_emi
            + invalid_outstanding
            + invalid_principal
            + invalid_dates
            + invalid_payment_dates
            + invalid_payment_amounts
            + invalid_payment_sequences
            + excess_payments
            + future_payments
        )

        self.stdout.write("")
        self.stdout.write("=" * 100)
        self.stdout.write("FINAL VALIDATION SUMMARY")
        self.stdout.write("=" * 100)

        self.stdout.write(f"Total loans: {total_loans}")
        self.stdout.write(
            f"Total loan payments: {total_payments}"
        )

        self.stdout.write("")

        self.stdout.write(
            f"Invalid EMI calculations: {invalid_emi}"
        )

        self.stdout.write(
            f"Invalid outstanding amounts: "
            f"{invalid_outstanding}"
        )

        self.stdout.write(
            f"Invalid principal amounts: "
            f"{invalid_principal}"
        )

        self.stdout.write(
            f"Invalid loan dates: {invalid_dates}"
        )

        self.stdout.write(
            f"Payments before loan start: "
            f"{invalid_payment_dates}"
        )

        self.stdout.write(
            f"Future payments: {future_payments}"
        )

        self.stdout.write(
            f"Wrong payment amounts: "
            f"{invalid_payment_amounts}"
        )

        self.stdout.write(
            f"Invalid payment sequences: "
            f"{invalid_payment_sequences}"
        )

        self.stdout.write(
            f"Loans with excess payments: "
            f"{excess_payments}"
        )

        self.stdout.write("")
        self.stdout.write(
            f"TOTAL VALIDATION ERRORS: {total_errors}"
        )

        self.stdout.write("=" * 100)

        if total_errors == 0:

            self.stdout.write(
                self.style.SUCCESS(
                    "FINAL LOAN DATA VALIDATION PASSED"
                )
            )

        else:

            self.stdout.write(
                self.style.ERROR(
                    "FINAL LOAN DATA VALIDATION FAILED"
                )
            )

    @staticmethod
    def calculate_simple_interest_emi(
        principal,
        interest_rate,
        tenure_years,
    ):

        simple_interest = (
            principal
            * interest_rate
            * Decimal(tenure_years)
            / Decimal("100")
        )

        total_payable = (
            principal
            + simple_interest
        )

        total_months = tenure_years * 12

        return (
            total_payable
            / Decimal(total_months)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )