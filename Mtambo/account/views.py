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
                
                # Determine user type and create corresponding profile
                user_type = request.data.get('user_type')
                
                if user_type == 'maintenance_company':
                    return self.create_maintenance_profile(request, user)
                elif user_type == 'technician':
                    return self.create_technician_profile(request, user)
                elif user_type == 'developer':
                    return self.create_developer_profile(request, user)
                
                return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        
        except serializers.ValidationError as ve:
            logger.error(f"Validation error in user signup: {ve}")
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.exception(f"Complete signup error: {e}")
            return Response(
                {"error": "Signup failed", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 
    @swagger_auto_schema(request_body=MaintenanceCompanyProfileSerializer)
    def create_maintenance_profile(self, request, user):
        company_name = request.data.get("company_name")
        company_address = request.data.get("company_address")
        registration_number = request.data.get("registration_number")  # Changed from company_registration_number
        specialization_name = request.data.get("specialization")
    
        if not all([company_name, company_address, registration_number, specialization_name]):
            return Response(
                {"error": "All fields are required for the Maintenance profile."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            maintenance_profile, created = MaintenanceCompanyProfile.objects.get_or_create(
                user=user,
                defaults={
                    'company_name': company_name,
                    'company_address': company_address,
                    'registration_number': registration_number,  # Changed field name
                    'specialization': specialization_name
                }
            )
        
            return Response({
                "user": UserSerializer(user).data,
                "maintenance_profile": MaintenanceCompanyProfileSerializer(maintenance_profile).data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"error": f"Error creating profile: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    @swagger_auto_schema(request_body=TechnicianProfileSerializer)
    def create_technician_profile(self, request, user):
        try:
            with transaction.atomic():  # Add atomic transaction
                # Validate required fields
                specialization = request.data.get("specialization")
                maintenance_company_id = request.data.get("maintenance_company_id")
            
                if not all([specialization, maintenance_company_id]):
                    return Response(
                        {"error": "Both specialization and maintenance_company_id are required."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
                # Check if the Maintenance company exists
                try:
                    maintenance_company = Maintenance.objects.get(id=maintenance_company_id)
                except Maintenance.DoesNotExist:
                    return Response(
                        {"error": f"Maintenance company with ID {maintenance_company_id} does not exist."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
                # Check if user already has a technician profile
                if hasattr(user, 'technician_profile'):
                    return Response(
                        {"error": "User already has a technician profile."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
                # Create Technician
                technician_serializer = TechnicianProfileSerializer(data={
                    'user': user.id,
                    'specialization': specialization,
                    'maintenance_company_id': maintenance_company.id
                })
            
                if technician_serializer.is_valid():
                    technician = technician_serializer.save()
                
                    # Create TechnicianProfile
                    technician_profile = TechnicianProfile.objects.create(
                        technician=technician
                    )
                
                    # Return complete response with all related data
                    return Response({
                        "user": UserSerializer(user).data,
                        "technician": TechnicianProfileSerializer(technician).data,
                        "technician_profile": TechnicianProfileSerializer(technician_profile).data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        technician_serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 

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
