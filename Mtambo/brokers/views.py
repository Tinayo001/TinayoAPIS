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


class MaintenanceCompaniesListView(APIView):
    """
    List all maintenance companies registered under a specific broker.
    If the broker doesn't exist or if there are no registered maintenance companies,
    appropriate messages will be returned.
    """
    permission_classes = [AllowAny]

    def get(self, request, broker_id: uuid.UUID):
        # Step 1: Get the broker by broker_id (UUID), or return a 404 if the broker doesn't exist
        broker = get_object_or_404(BrokerUser, id=broker_id)

        # Step 2: Retrieve all maintenance companies registered under this broker
        # The BrokerReferral model links brokers and maintenance companies via UUID
        broker_referrals = BrokerReferral.objects.filter(broker=broker)

        # Step 3: Check if the broker has any maintenance companies registered
        if not broker_referrals.exists():
            return Response(
                {"message": f"No maintenance companies are registered under broker with ID {broker_id}."},
                status=status.HTTP_200_OK  # Return 200 OK since it's a valid request, just no data
            )

        # Step 4: Collect the maintenance companies associated with the broker
        maintenance_companies = [referral.maintenance_company for referral in broker_referrals]
        
        # Step 5: Serialize the maintenance companies using the appropriate serializer
        serialized_maintenance_companies = MaintenanceCompanyProfileSerializer(maintenance_companies, many=True)

        return Response(
            {
                "broker_id": broker.id,  # Return the broker's UUID as an identifier
                "broker_email": broker.email,  # Include the broker's email for additional identification
                "broker_referral_code": broker.referral_code,  # Include referral code
                "maintenance_companies": serialized_maintenance_companies.data
            },
            status=status.HTTP_200_OK
        )
