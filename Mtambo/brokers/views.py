from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # For testing purposes
# from rest_framework.permissions import IsAuthenticated  # For production
from .serializers import BrokerRegistrationSerializer
from .models import *
from maintenance_companies.serializers import MaintenanceCompanyProfile, MaintenanceCompanyProfileSerializer, MaintenanceListSerializer
from django.shortcuts import get_object_or_404

import logging
logger = logging.getLogger(__name__)


class BrokerRegistrationView(APIView):
    """
    API endpoint for broker registration.
    - For testing: AllowAny permission.
    - For production: Only admin users can register brokers (commented out).
    """
    permission_classes = [AllowAny]  # For testing purposes
    # permission_classes = [IsAuthenticated]  # For production

    @swagger_auto_schema(
        operation_description="Register a new broker",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Broker's username"),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Broker's email"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description="Broker's password"),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description="Broker's first name"),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description="Broker's last name"),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description="Broker's phone number"),
            }
        ),
        responses={
            201: openapi.Response(
                description="Broker registered successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'field_name': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        )
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        # For production: Check if the requesting user is an admin (is_staff)
        # if not request.user.is_staff:
        #     return Response(
        #         {"error": "Only admin users can register brokers."},
        #         status=status.HTTP_403_FORBIDDEN
        #     )
        serializer = BrokerRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Save the broker user
            return Response(
                {"message": "Broker registered successfully.", "data": serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BrokerListView(APIView):
    """
    API endpoint to list all registered brokers with no authentication required.
    """
    permission_classes = [AllowAny]  # Allow unrestricted access to this view

    def get(self, request, *args, **kwargs):
        brokers = BrokerUser.objects.all()  # Get all brokers
        serializer = BrokerRegistrationSerializer(brokers, many=True)  # Serialize the data
        return Response(serializer.data, status=status.HTTP_200_OK)


class BrokerMaintenanceCompaniesView(APIView):
    def get(self, request, broker_id):
        try:
            # Using the correct relationship path through referral
            maintenance_companies = MaintenanceCompanyProfile.objects.filter(
                referral__broker_id=broker_id
            )
            
            if not maintenance_companies.exists():
                return Response({
                    "message": f"No maintenance companies are registered under broker with ID {broker_id}."
                })
            serializer = MaintenanceCompanyProfileSerializer(maintenance_companies, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.exception("Error fetching broker's maintenance companies")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
