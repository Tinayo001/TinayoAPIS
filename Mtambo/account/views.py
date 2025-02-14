import uuid
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny  # Allow any user to access these endpoints
from .models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from developers.models import DeveloperProfile
from maintenance_companies.serializers import MaintenanceCompanyProfileSerializer
from technicians.serializers import TechnicianProfileSerializer
from developers.serializers import DeveloperProfileSerializer
from .serializers import UserSerializer, LoginSerializer
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db import transaction
from rest_framework import serializers
from typing import Dict, List, Tuple, Optional, Any
from alerts.models import AlertType
from alerts.services import AlertService
from alerts.models import Alert
from brokers.models import BrokerUser
from brokers.models import BrokerReferral
from brokers.models import BrokerUserManager
from payments.models import PaymentSettings
from maintenance_companies.serializers import MaintenanceCompanyProfileSerializer

import logging
logger = logging.getLogger(__name__)

# View for User SignUp
class SignUpView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=UserSerializer)
    def post(self, request):
        user_serializer = UserSerializer(data=request.data)
        
        try:
            if user_serializer.is_valid(raise_exception=True):
                user = user_serializer.save()
                
                # Check account_type since that's what your request uses
                account_type = request.data.get('account_type')
                
                if account_type == 'maintenance':
                    return self.create_maintenance_profile(request, user)
                elif account_type == 'technician':
                    return self.create_technician_profile(request, user)
                elif account_type == 'developer':
                    return self.create_developer_profile(request, user)
                
                return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.exception(f"Signup error: {e}")
            return Response(
                {"error": "Signup failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create_maintenance_profile(self, request, user, referral_code=None):
        # Get referral code from request data if not passed directly
        if not referral_code:
            referral_code = request.data.get('referral_code')
    
        logger.info(f"DEBUG: Starting profile creation with referral_code: {referral_code}")
    
        # Handle the maintenance user profile creation
        company_name = request.data.get("company_name")
        company_address = request.data.get("company_address")
        company_registration_number = request.data.get("registration_number")
        specialization_name = request.data.get("specialization")

        if not all([company_name, company_address, company_registration_number, specialization_name]):
            logger.error("Missing required fields")
            return Response(
                {"error": "All fields are required for the Maintenance profile."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create or update the Maintenance profile
            maintenance_profile, created = MaintenanceCompanyProfile.objects.get_or_create(user=user)
            maintenance_profile.company_name = company_name
            maintenance_profile.company_address = company_address
            maintenance_profile.company_registration_number = company_registration_number
            maintenance_profile.specialization = specialization_name
            maintenance_profile.save()
        
            logger.info(f"DEBUG: Maintenance profile created/updated: {maintenance_profile.id}")

            # Step 2: Process the referral if referral_code is provided
            if referral_code:
                logger.info(f"DEBUG: Processing referral code: {referral_code}")
            
                # Look for the broker using the referral code
                broker = BrokerUser.objects.filter(referral_code=referral_code).first()
            
                if not broker:
                    logger.error(f"Broker not found for referral code: {referral_code}")
                    return Response(
                        {"error": f"Invalid referral code: {referral_code}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                logger.info(f"DEBUG: Found broker: {broker.email}")

                # Check for existing referral
                existing_referral = BrokerReferral.objects.filter(
                    maintenance_company=maintenance_profile
                ).exists()

                if existing_referral:
                    logger.warning(f"Maintenance company already has a referral")
                    return Response(
                        {"error": "This maintenance company already has a broker referral."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    # Get commission values from PaymentSettings if they exist, otherwise use broker defaults
                    payment_settings = PaymentSettings.objects.first()
                    if payment_settings:
                        commission_percentage = payment_settings.default_commission
                        commission_duration_months = payment_settings.default_commission_duration
                    else:
                        # Use broker's default values from the model
                        commission_percentage = broker.commission_percentage
                        commission_duration_months = broker.commission_duration_months
                        logger.info(f"Using broker default values: {commission_percentage}% for {commission_duration_months} months")

                    # Create the referral entry
                    referral = BrokerReferral.objects.create(
                        broker=broker,
                        maintenance_company=maintenance_profile,
                        commission_percentage=commission_percentage,
                        commission_duration_months=commission_duration_months,
                    )
                
                    logger.info(f"DEBUG: Successfully created broker referral with ID: {referral.id}")

                    return Response({
                        "user": UserSerializer(user).data,
                        "maintenance_profile": MaintenanceCompanyProfileSerializer(maintenance_profile).data,
                        "broker_referral": {
                            "id": str(referral.id),
                            "broker_email": broker.email,
                            "commission_percentage": float(commission_percentage),
                            "commission_duration_months": commission_duration_months
                        },
                        "message": f"Successfully registered under broker {broker.email} with commission rate of {commission_percentage}%."
                    }, status=status.HTTP_201_CREATED)

                except Exception as e:
                    logger.error(f"Failed to create broker referral: {str(e)}")
                    return Response(
                        {"error": f"Failed to create broker referral: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # If no referral code or referral processing failed
            return Response({
                "user": UserSerializer(user).data,
                "maintenance_profile": MaintenanceCompanyProfileSerializer(maintenance_profile).data,
                "message": "Successfully registered maintenance company without a referral."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error in profile creation: {str(e)}")
            return Response(
                {"error": f"Failed to create maintenance profile: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(request_body=TechnicianProfileSerializer)
    def create_technician_profile(self, request, user):
        try:
            with transaction.atomic():
                # Get and validate maintenance company first
                maintenance_company_id = request.data.get("maintenance_company_id")
                if not maintenance_company_id:
                    return Response({"error": "Maintenance company ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
                maintenance_company = MaintenanceCompanyProfile.objects.get(id=maintenance_company_id)
            
                # Create technician with explicit company assignment
                technician_data = request.data.copy()
                technician_data['maintenance_company'] = maintenance_company  # Make sure this relationship is set
                technician_serializer = TechnicianProfileSerializer(data=technician_data)
            
                if not technician_serializer.is_valid():
                    return Response(technician_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
                # Save technician with transaction
                technician = technician_serializer.save()
            
                # Create alert exactly like in the working view
                alert = AlertService.create_alert(
                    alert_type=AlertType.TECHNICIAN_SIGNUP,
                    recipient=maintenance_company.user,  # Direct reference to company instance
                    related_object=technician,      # Direct reference to technician instance
                    message=f"New technician {technician.user.first_name} {technician.user.last_name} has signed up and requires approval"
                )
            
                return Response({"message": "Technician profile created successfully"}, status=status.HTTP_201_CREATED)
            
        except MaintenanceCompanyProfile.DoesNotExist:
            return Response({"error": "Maintenance company not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception("Technician signup failed")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
       
 
    @swagger_auto_schema(request_body=DeveloperProfileSerializer)
    def create_developer_profile(self, request, user):
        # Handle the developer user profile creation
        developer_name = request.data.get("developer_name")
        address = request.data.get("address")

        # Ensure both developer_name and address are provided
        if not all([developer_name, address]):
            return Response(
                {"error": "Both developer_name and address are required for the Developer profile."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create Developer profile
        developer_profile = Developer.objects.create(
            user=user,
            developer_name=developer_name,
            address=address
        )

        # Return response with user and developer profile data
        return Response(
            {"user": UserSerializer(user).data, "developer_profile": DeveloperSerializer(developer_profile).data},
            status=status.HTTP_201_CREATED
        )
    

# account/views.py
class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=LoginSerializer,
        responses={200: 'Login successful', 400: 'Bad request', 401: 'Unauthorized'}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            email_or_phone = serializer.validated_data['email_or_phone']
            password = serializer.validated_data['password']
            
            print("Attempting authentication...")
            user = authenticate(request, username=email_or_phone, password=password)
            print(f"Authentication result: {user}")

            if user is None:  # Changed this condition to check for None explicitly
                return Response(
                    {"error": "Invalid credentials"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            
            if user is not None:
                # Generate the tokens for the user
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                # Determine the account type based on the user's related profile
                account_type = None
                profile_id = None
                if hasattr(user, 'developer_profile'):
                    account_type = 'developer'
                    profile_id = user.developer_profile.id
                elif hasattr(user, 'maintenance_profile'):
                    account_type = 'maintenance'
                    profile_id = user.maintenance_profile.id
                elif hasattr(user, 'technician_profile'):
                    account_type = 'technician'
                    profile_id = user.technician_profile.id

                # Prepare the user data for the response
                user_data = {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone_number': user.phone_number,  # Assuming the User model has a 'phone_number' field
                    'account_type': account_type,
                    'created_at': user.created_at,
                    'is_staff': user.is_staff,
                    'access': str(access_token),
                    'refresh': str(refresh),
                    'account_type_id': profile_id,
                    'user_id': user.id

                }

                # Return the response with user data and tokens
                return Response(user_data, status=status.HTTP_200_OK)
            
            # Invalid credentials
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # If the serializer is not valid, return the validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



# View to List Available Specializations (for Frontend Dropdown)
class SpecializationListView(APIView):
    permission_classes = [AllowAny]  # Allow any user to access this endpoint

    @swagger_auto_schema(
        operation_summary="List Available Specializations",
        operation_description="Fetches a list of specializations that can be displayed in dropdowns or UI forms.",
        responses={
            200: openapi.Response(
                description="List of specializations",
                examples={
                    "application/json": {
                        "option1": "Elevators",
                        "option2": "HVAC",
                        "option3": "Power Backup Generators"
                    }
                }
            )
        }
    )
    def get(self, request):
        # Define the specializations as a dictionary with formatted options
        specializations = {
            "option1": "Elevators",
            "option2": "HVAC",
            "option3": "Power Backup Generators"
        }

        # Return the specializations in the response with a 200 OK status
        return Response(specializations, status=status.HTTP_200_OK)
