from django.urls import path

from apps.loans.views import (
    CustomerLoansAPIView,
    LoanPaymentHistoryAPIView,
)

urlpatterns = [

    path(
        "",
        CustomerLoansAPIView.as_view(),
        name="customer-loans",
    ),

    path(
        "payments/",
        LoanPaymentHistoryAPIView.as_view(),
        name="loan-payment-history",
    ),

]