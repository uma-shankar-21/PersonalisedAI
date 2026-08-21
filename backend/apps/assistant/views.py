from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.assistant.services.chat_service import (
    ChatService,
)


class AssistantChatAPIView(
    APIView
):

    def post(
        self,
        request,
    ):

        customer_id = (
            request.data.get(
                "customer_id"
            )
        )

        message = (
            request.data.get(
                "message"
            )
        )

        if not customer_id:

            return Response(
                {
                    "error": (
                        "customer_id is required"
                    )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        if not message:

            return Response(
                {
                    "error": (
                        "message is required"
                    )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        chat_service = (
            ChatService()
        )

        result = (
            chat_service.chat(
                customer_id=customer_id,
                message=message,
            )
        )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )