from django.urls import path

from apps.transactions.views import (
    TransactionSearchAPIView,
)


urlpatterns = [

    path(
        "search/",
        TransactionSearchAPIView.as_view(),
        name="transaction-search",
    ),

]