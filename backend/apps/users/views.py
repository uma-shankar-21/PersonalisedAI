from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer

from .serializers import (
    CustomerCreateSerializer,
    CustomerSerializer,LoginSerializer
)
from .services.user_service import create_customer,get_customer,login_customer


class CustomerCreateView(APIView):

    def post(self, request):
        serializer = CustomerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        customer = create_customer(serializer.validated_data)

        return Response(
            CustomerSerializer(customer).data,
            status=status.HTTP_201_CREATED,
        )

class CustomerDetailView(APIView):

    def get(self, request, customer_id):

        customer = get_customer(customer_id)

        if customer is None:
            return Response(
                {
                    "error": "Customer not found",
                    "customer_id": str(customer_id),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CustomerSerializer(customer).data,
            status=status.HTTP_200_OK,
        )

class CustomerLoginView(APIView):

    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = login_customer(
            identifier=serializer.validated_data["identifier"],
            password=serializer.validated_data["password"],
        )

        if result is None:
            return Response(
                {
                    "error": "Invalid credentials."
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response(
            {
                "message": "Login successful.",
                "customer": CustomerSerializer(
                    result["customer"]
                ).data,
                "access": result["access"],
                "refresh": result["refresh"],
            },
            status=status.HTTP_200_OK,
        )