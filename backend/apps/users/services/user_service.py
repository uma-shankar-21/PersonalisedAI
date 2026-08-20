from django.contrib.auth.models import User
from django.db import transaction

from ..models import Customer
from django.contrib.auth import authenticate

from rest_framework_simplejwt.tokens import RefreshToken

@transaction.atomic
def create_customer(data):
    user = User.objects.create_user(
        username=data["username"],
        email=data["email"],
        password=data["password"],
    )

    customer = Customer.objects.create(
        user=user,
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
        date_of_birth=data.get("date_of_birth"),
    )

    return customer

def get_customer(customer_id):
    try:
        return Customer.objects.select_related("user").get(
            id=customer_id
        )
    except Customer.DoesNotExist:
        return None

def login_customer(identifier, password):

    user = User.objects.filter(email__iexact=identifier).first()

    if user is None:
        user = User.objects.filter(username=identifier).first()

    if user is None:
        return None

    authenticated_user = authenticate(
        username=user.username,
        password=password,
    )

    if authenticated_user is None:
        return None

    if not authenticated_user.is_active:
        return None

    refresh = RefreshToken.for_user(authenticated_user)

    customer = authenticated_user.customer

    return {
        "customer": customer,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }