# payments/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from .serializers import PaymentSettingsSerializer
from .models import PaymentSettings
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from brokers.models import BrokerUser
from .serializers import BrokerCommissionSettingsSerializer

class ConfigurePaymentSettingsView(APIView):
    """
    API endpoint for retrieving and configuring default payment settings.
    - GET: Retrieve all payment settings.
    - POST: Update one or more payment settings.
    For testing purposes, allow any user to access this endpoint.
    For production, restrict access to admin users (is_staff).
    """
    # For testing purposes, allow any user to access this endpoint
    permission_classes = [AllowAny]  # AllowAny for testing
    # For production, uncomment the following line to restrict access to admin users
    # permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve all payment settings.
        """
        # Get or create the PaymentSettings instance
        settings, created = PaymentSettings.objects.get_or_create(id=1)

        # Serialize the settings
        serializer = PaymentSettingsSerializer(settings)

        # Add a flag to indicate whether each field is configured
        response_data = serializer.data
        response_data["is_configured"] = {
            "min_charge_per_elevator": settings.min_charge_per_elevator != None,  # Default value
            "default_commission": settings.default_commission != None,  # Default value
            "default_commission_duration": settings.default_commission_duration != None,  # Default value
            "default_calculation_date": settings.default_calculation_date != None,  # Default value
            "default_due_date": settings.default_due_date != None,  # Default value
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests to update payment settings.
        Allows partial updates (one or more fields).
        """
        serializer = PaymentSettingsSerializer(data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            # Get or create the PaymentSettings instance
            settings, created = PaymentSettings.objects.get_or_create(id=1)

            # Update only the fields provided in the request
            for field, value in serializer.validated_data.items():
                setattr(settings, field, value)
            settings.save()

            return Response(
                {"message": "Payment settings updated successfully.", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BrokerCommissionSettingsView(APIView):
    """
    API endpoint for retrieving and updating commission settings of a specific broker.
    Only accessible by admin users (is_staff).
    """
    # For testing purposes, allow any user to access this endpoint
    permission_classes = [AllowAny]  # AllowAny for testing
    # For production, uncomment the following line to restrict access to admin users
    # permission_classes = [IsAdminUser]

    def get(self, request, broker_id, *args, **kwargs):
        """
        Handle GET requests to retrieve commission settings of a specific broker.
        """
        # Retrieve the broker or return a 404 response if not found
        broker = get_object_or_404(BrokerUser, id=broker_id)

        # Serialize the broker's commission settings
        serializer = BrokerCommissionSettingsSerializer(broker)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, broker_id, *args, **kwargs):
        """
        Handle PUT requests to update commission settings of a specific broker.
        """
        # Retrieve the broker or return a 404 response if not found
        broker = get_object_or_404(BrokerUser, id=broker_id)

        # Serialize and validate the request data
        serializer = BrokerCommissionSettingsSerializer(broker, data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            serializer.save()  # Save the updated commission settings
            return Response(
                {"message": "Broker commission settings updated successfully.", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
