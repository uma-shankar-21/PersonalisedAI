from django.urls import path

from apps.banking.views import (
    CustomerBankAccountsAPIView,
)

urlpatterns = [

    path(
        "accounts/",
        CustomerBankAccountsAPIView.as_view(),
        name="customer-accounts",
    ),

]