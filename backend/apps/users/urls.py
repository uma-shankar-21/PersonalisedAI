from django.urls import path

from .views import CustomerCreateView, CustomerDetailView, CustomerLoginView

urlpatterns = [
    path(
        "<uuid:customer_id>/",
        CustomerDetailView.as_view(),
        name="customer-detail",
    ),
    path(
        "login/",
        CustomerLoginView.as_view(),
        name="customer-login",
    ),
    path("create/", CustomerCreateView.as_view(), name="customer-create"),
]