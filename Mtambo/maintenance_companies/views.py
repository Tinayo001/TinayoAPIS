from django.db import DatabaseError
from datetime import datetime
from django.http import Http404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import PermissionDenied, NotAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.core.exceptions import ObjectDoesNotExist
import uuid
from uuid import UUID
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from django.shortcuts import render,get_object_or_404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.generics import UpdateAPIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ValidationError as DjangoValidationError
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

from .models import MaintenanceCompanyProfile
from account.models import User
from developers.serializers import DeveloperProfileSerializer
from .serializers import MaintenanceCompanyProfileSerializer, AddBuildingSerializer
from technicians.serializers import TechnicianProfileSerializer
from technicians.serializers import TechnicianListSerializer, TechnicianDetailSerializer

from api.authentication import Custom401SessionAuthentication, Custom401JWTAuthentication
from buildings.models import Building
from elevators.models import Elevator
from technicians.models import TechnicianProfile
from developers.models import DeveloperProfile
from developers.serializers import DeveloperDetailSerializer
from buildings.serializers import BuildingSerializer
from elevators.serializers import ElevatorSerializer, ElevatorReadSerializer, ElevatorCreateSerializer

from jobs.models import MaintenanceSchedule

class MaintenanceCompanyListView(generics.ListAPIView):
    """
    API endpoint that allows viewing a list of all maintenance companies.
    GET /maintenance/companies/
    """
    permission_classes = [AllowAny]
    queryset = MaintenanceCompanyProfile.objects.all()
    serializer_class = MaintenanceCompanyProfileSerializer

class MaintenanceCompanyDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve detailed information about a specific maintenance company.
    GET /maintenance/companies/{uuid_id}/
    """
    permission_classes = [AllowAny]
    serializer_class = MaintenanceCompanyProfileSerializer

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'uuid_id', 
                openapi.IN_PATH, 
                description="UUID ID of the maintenance company", 
                required=True, 
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID
            )
        ],
        operation_summary="Retrieve company profile by UUID",
        operation_description="Retrieve company profile by UUID, creating one if it doesn't exist. "
                            "First tries direct profile lookup, then falls back to maintenance company lookup.",
        responses={
            200: MaintenanceCompanyProfileSerializer,
            400: 'Invalid UUID format',
            404: 'Company not found',
        }
    )
    def get_object(self):
        """
        Retrieve company profile by UUID, creating one if it doesn't exist.
        First tries direct profile lookup, then falls back to maintenance company lookup.
        """
        uuid_id = self.kwargs.get('uuid_id')
        
        if not uuid_id:
            raise NotFound("UUID ID not provided")
            
        # Validate UUID format
        try:
            uuid_obj = uuid.UUID(str(uuid_id))
        except (ValueError, TypeError):
            raise ValidationError("Invalid UUID format")
            
        try:
            # Primary lookup: Try to find existing profile
            return MaintenanceCompanyProfile.objects.get(id=uuid_obj)
        except MaintenanceCompanyProfile.DoesNotExist:
            try:
                # Secondary lookup: Find maintenance and get/create profile
                maintenance = MaintenanceCompanyProfile.objects.get(id=uuid_obj)
                profile, created = MaintenanceCompanyProfile.objects.get_or_create(
                    maintenance=maintenance
                )
                return profile
            except MaintenanceCompanyProfile.DoesNotExist:
                raise NotFound("Company not found")

class ListPendingTechniciansView(generics.ListAPIView):
    """
    API endpoint to list all pending (unapproved) technicians for a maintenance company.
    GET /maintenance/companies/{company_id}/pending-technicians/
    """
    permission_classes = [AllowAny]
    serializer_class = TechnicianListSerializer

    def get_queryset(self):
        """
        Retrieve all unapproved technicians for the specified company.
        """
        company_id = self.kwargs.get('company_id')
        company = get_object_or_404(MaintenanceCompanyProfile, id=company_id)
        return TechnicianProfile.objects.filter(
            maintenance_company=company_id,
            is_approved=False
        )

    def get(self, request, *args, **kwargs):
        """
        Return list of pending technicians with their basic information.
        """
        queryset = self.get_queryset()
        pending_technicians = [{
            "id": str(tech.id),
            "name": f"{tech.user.first_name} {tech.user.last_name}",
            "email": tech.user.email,
            "specialization": tech.specialization,
        } for tech in queryset]

        return Response({
            "pending_technicians": pending_technicians,
            "count": len(pending_technicians)
        }, status=status.HTTP_200_OK)

class CompanyAddTechnicianView(APIView):
    """
    API endpoint to approve a pending technician for a maintenance company.
    POST /companies/technicians/{technician_id}/approve/
    """
    permission_classes = [AllowAny]
    
    def post(self, request, technician_id):
        try:
            # Get the technician instance
            technician = TechnicianProfile.objects.get(id=technician_id)
            
            # Check if technician is already approved
            if technician.is_approved:
                return Response({
                    "error": "Technician is already approved"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Approve the technician
            technician.is_approved = True
            technician.approved_at = timezone.now()
            technician.save()
            
            # Return success response with technician details
            return Response({
                "message": "Technician successfully approved",
                "technician": {
                    "id": str(technician.id),
                    "name": f"{technician.user.first_name} {technician.user.last_name}",
                    "email": technician.user.email,
                    "specialization": technician.specialization,
                    "approved_at": technician.approved_at,
                }
            }, status=status.HTTP_200_OK)
            
        except TechnicianProfile.DoesNotExist:
            return Response({
                "error": "Technician not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": f"An error occurred while approving the technician: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
class UpdateMaintenanceCompanyView(generics.UpdateAPIView):
    """
    API endpoint to update maintenance company details.
    PATCH /maintenance/companies/{uuid_id}/
    """
    queryset = MaintenanceCompanyProfile.objects.all()
    serializer_class = MaintenanceCompanyProfileSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    lookup_url_kwarg = 'uuid_id'

    http_method_names = ['put']  # Only allow PATCH

    def get_object(self):
        try:
            return MaintenanceCompanyProfile.objects.get(id=self.kwargs['uuid_id'])
        except MaintenanceCompanyProfile.DoesNotExist:
            raise NotFound(detail="Maintenance company not found.")
        except ValueError:
            raise ValidationError(detail="Invalid UUID provided.")

class MaintenanceCompanyBySpecializationView(generics.ListAPIView):
    """
    API endpoint to list maintenance companies filtered by specialization.
    GET /specialization/{specialization}/
    """
    permission_classes = [AllowAny]
    serializer_class = MaintenanceCompanyProfileSerializer

    def get_queryset(self):
        """
        Filter maintenance companies by the specified specialization.
        Case-insensitive and ignores invalid input.
        """
        specialization = self.kwargs.get('specialization', '').strip()
        
        # Validate specialization parameter, ensuring it is a non-empty, alphabetic string
        if not specialization or not specialization.isalpha():
            return MaintenanceCompanyProfile.objects.none()  # Return empty queryset for invalid input
        
        # Filter by specialization (case-insensitive)
        return MaintenanceCompanyProfile.objects.filter(specialization__iexact=specialization)

    def list(self, request, *args, **kwargs):
        """
        Return a filtered list of companies with only ID and company name fields.
        """
        queryset = self.get_queryset()

        # If no companies are found, return an empty list with a 200 OK status
        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        # Serialize the data and filter only the necessary fields (id and company_name)
        serialized_data = self.serializer_class(queryset, many=True).data
        filtered_data = [
            {
                "id": item["id"],  # Assuming `id` field exists in the serializer output
                "company_name": item["company_name"]  # Assuming `company_name` field exists in the serializer output
            }
            for item in serialized_data
        ]

        return Response(filtered_data, status=status.HTTP_200_OK)

class MaintenanceCompanyByEmailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = MaintenanceCompanyProfileSerializer
    
    def get_object(self):
        email = self.kwargs['email']
        try:
            user = User.objects.get(email=email)
            # Check if the user has an associated maintenance profile
            if not user or not hasattr(user, 'maintenance_profile'):
                raise NotFound(detail="User has no maintenance company associated.")
            return user.maintenance_profile  # This will return the associated Maintenance object
        except User.DoesNotExist:
            raise NotFound(detail="User with this email not found.")

class MaintenanceCompanyTechniciansView(generics.ListAPIView):
    """
    API endpoint to list all technicians associated with a specific maintenance company.
    GET /maintenance/companies/{uuid_id}/technicians/
    """
    permission_classes = [AllowAny]
    serializer_class = TechnicianListSerializer
    
    def get_queryset(self):
        """
        Retrieve all technicians linked to the specified maintenance company.
        """
        uuid_id = self.kwargs.get('uuid_id')
        try:
            company_profile = MaintenanceCompanyProfile.objects.get(id=uuid_id)
            return TechnicianProfile.objects.filter(maintenance_company=company_profile)
        except MaintenanceCompanyProfile.DoesNotExist:
            raise NotFound("Maintenance company not found")

class RemoveTechnicianFromCompanyView(APIView):
    permission_classes = [AllowAny]
    
    def delete(self, request, maintenance_company_id, technician_id):
        try:
            # Get the maintenance company by ID
            maintenance_company = get_object_or_404(MaintenanceCompanyProfile, id=maintenance_company_id)
            
            try:
                # Get the technician by ID
                technician = get_object_or_404(TechnicianProfile, id=technician_id)
            except Http404:
                return Response(
                    {"error": f"Technician with ID {technician_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if the technician is part of the given maintenance company
            if technician.maintenance_company != maintenance_company:
                return Response(
                    {"error": "Technician does not belong to this company"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Remove the technician from the maintenance company
            technician.maintenance_company = None
            technician.save(update_fields=['maintenance_company'])
            
            return Response(
                {"message": "Technician successfully removed from company"},
                status=status.HTTP_200_OK
            )
            
        except Http404:
            return Response(
                {"error": f"Maintenance company with ID {maintenance_company_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log the error (optional, can be removed if not needed)
            print(f"Error in RemoveTechnicianFromCompanyView: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AddBuildingView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [Custom401SessionAuthentication, Custom401JWTAuthentication]

    @swagger_auto_schema(
        operation_description="Add a new building with one or more elevators",
        manual_parameters=[
            openapi.Parameter('company_uuid', openapi.IN_PATH, 
                description="UUID of the maintenance company", type=openapi.TYPE_STRING),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['developer_uuid', 'name', 'address', 'contact', 'elevators'],
            properties={
                'developer_uuid': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="UUID of the developer"
                ),
                'name': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Building name"
                ),
                'address': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Building address"
                ),
                'contact': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description="Building contact information"
                ),
                'elevators': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="List of elevators",
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=[
                            'user_name', 'capacity', 'machine_number', 
                            'manufacturer', 'installation_date'
                        ],
                        properties={
                            'user_name': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                description="Elevator user name"
                            ),
                            'capacity': openapi.Schema(
                                type=openapi.TYPE_NUMBER, 
                                description="Elevator capacity"
                            ),
                            'machine_number': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                description="Unique machine number"
                            ),
                            'manufacturer': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                description="Elevator manufacturer"
                            ),
                            'installation_date': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                description="Installation date (YYYY-MM-DD)"
                            ),
                            'technician_id': openapi.Schema(
                                type=openapi.TYPE_STRING, 
                                description="Optional technician UUID"
                            )
                        }
                    )
                )
            }
        )
    )
    def put(self, request, company_uuid: UUID):
        # Step 0: Validate required fields first
        required_fields = {
            "developer_uuid": request.data.get("developer_uuid"),
            "name": request.data.get("name"),
            "address": request.data.get("address"),
            "contact": request.data.get("contact"),
            "elevators": request.data.get("elevators")
        }

        errors = {}
        for field, value in required_fields.items():
            if not value:
                errors[field] = ["This field is required."]
            elif field == "elevators" and not isinstance(value, list):
                errors[field] = ["A list of elevators is required."]
        
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Step 1: Retrieve the Maintenance company
        try:
            company = MaintenanceCompanyProfile.objects.get(id=company_uuid)
        except (MaintenanceCompanyProfile.DoesNotExist, ValidationError, ValueError):
            return Response(
                {"error": "Company not found or invalid UUID format"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 2: Validate developer UUID
        try:
            developer = DeveloperProfile.objects.get(id=required_fields["developer_uuid"])
        except (DeveloperProfile.DoesNotExist, ValidationError, ValueError):
            return Response(
                {"developer_uuid": ["Developer not found or invalid UUID format"]}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Step 3: Validate elevators data
        elevators_data = required_fields["elevators"]
        elevator_errors = []
        
        for index, elevator_data in enumerate(elevators_data):
            required_elevator_fields = [
                'user_name', 'capacity', 'machine_number', 
                'manufacturer', 'installation_date'
            ]
            errors = {}
            
            for field in required_elevator_fields:
                if not elevator_data.get(field):
                    errors[field] = ["This field is required."]

            # Check duplicate machine number
            machine_number = elevator_data.get("machine_number")
            if machine_number and Elevator.objects.filter(machine_number=machine_number).exists():
                errors["machine_number"] = [
                    f"Elevator with machine number {machine_number} already exists."
                ]

            # Validate installation date
            installation_date = elevator_data.get("installation_date")
            try:
                if isinstance(installation_date, str):
                    datetime.strptime(installation_date, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                errors["installation_date"] = ["Invalid date format. Use YYYY-MM-DD."]

            if errors:
                elevator_errors.append({f"elevator_{index}": errors})

        if elevator_errors:
            return Response(
                {"elevators": elevator_errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Step 4: Create building
            new_building = Building.objects.create(
                name=required_fields["name"],
                address=required_fields["address"],
                contact=required_fields["contact"],
                developer=developer
            )

            # Step 5: Create elevators
            created_elevators = []
            for elevator_data in elevators_data:
                # Validate technician if provided
                technician = None
                technician_id = elevator_data.get("technician_id")
                if technician_id:
                    try:
                        technician = TechnicianProfile.objects.get(
                            id=technician_id, 
                            maintenance_company=company
                        )
                    except (TechnicianProfile.DoesNotExist, ValidationError, ValueError):
                        return Response(
                            {"elevators": {"technician_id": ["Technician not found or invalid UUID format"]}}, 
                            status=status.HTTP_404_NOT_FOUND
                        )

                # Create elevator
                installation_date = datetime.strptime(
                    elevator_data["installation_date"], 
                    "%Y-%m-%d"
                ).date()
                
                new_elevator = Elevator.objects.create(
                    user_name=elevator_data["user_name"],
                    capacity=elevator_data["capacity"],
                    machine_number=elevator_data["machine_number"],
                    manufacturer=elevator_data["manufacturer"],
                    installation_date=installation_date,
                    building=new_building,
                    maintenance_company=company,
                    technician=technician,
                    developer=developer
                )

                created_elevators.append({
                    "id": str(new_elevator.id),
                    "user_name": new_elevator.user_name,
                    "machine_number": new_elevator.machine_number,
                    "capacity": new_elevator.capacity,
                    "manufacturer": new_elevator.manufacturer,
                    "installation_date": new_elevator.installation_date.isoformat(),
                    "technician": {
                        "id": str(technician.id) if technician else None,
                        "name": (f"{technician.user.first_name} {technician.user.last_name}" 
                               if technician else None)
                    }
                })

            # Return response data
            return Response({
                "id": str(new_building.id),
                "name": new_building.name,
                "address": new_building.address,
                "contact": new_building.contact,
                "developer": {
                    "id": str(developer.id),
                    "developer_name": developer.developer_name
                },
                "elevators": created_elevators
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Log the error for debugging
            logger.error(f"Error creating building and elevators: {str(e)}")
            return Response(
                {"error": "Failed to create building and elevators"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BuildingListView(generics.ListAPIView):
    """Retrieve a list of buildings linked to a maintenance company."""
    permission_classes = [AllowAny]
    serializer_class = BuildingSerializer

    def get_queryset(self):
        company_id = self.kwargs['company_id']
        try:
            company = MaintenanceCompanyProfile.objects.get(id=company_id)
        except MaintenanceCompanyProfile.DoesNotExist:
            raise NotFound("Maintenance company not found.")
        
        return Building.objects.filter(elevators__maintenance_company=company).distinct()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No buildings found for this maintenance company."},
                status=status.HTTP_200_OK
            )
        return super().list(request, *args, **kwargs)

class BuildingDetailView(APIView):
    permission_classes = [AllowAny]  # Modify as necessary for permissions

    def get(self, request, company_id, building_id):
        try:
            # Step 1: Retrieve the maintenance company using the company_id
            company = MaintenanceCompanyProfile.objects.get(id=company_id)

            # Step 2: Get all elevators under the given maintenance company
            elevators = Elevator.objects.filter(maintenance_company=company)

            # Step 3: Retrieve the building using the building_id
            building = Building.objects.get(id=building_id)

            # Step 4: Ensure the building has elevators linked to the company
            if not elevators.filter(building=building).exists():
                raise NotFound(detail="Building is not linked to the specified maintenance company.", code=404)

            # Step 5: Serialize and return the building data
            serialized_data = BuildingSerializer(building)
            return Response(serialized_data.data, status=status.HTTP_200_OK)

        except MaintenanceCompanyProfile.DoesNotExist:
            return Response(
                {"error": "Maintenance company not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Building.DoesNotExist:
            return Response(
                {"error": "Building not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except NotFound as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DevelopersUnderCompanyView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, company_id):
        # Step 1: Check if the company_id is a valid UUID string
        try:
            # Ensure the company_id is treated as a string for validation
            company_id = str(company_id)  # Make sure it's a string
            valid_uuid = uuid.UUID(company_id)  # This will raise ValueError if the format is invalid
        except ValueError:
            return Response(
                {"error": "Invalid company ID format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Step 2: Retrieve the maintenance company by its ID
            company = MaintenanceCompanyProfile.objects.get(id=company_id)
            
            # Step 3: Get buildings with elevators maintained by this company
            buildings = Building.objects.filter(
                elevators__maintenance_company=company
            ).distinct()
            
            # Step 4: Get developers associated with these buildings
            developers = DeveloperProfile.objects.filter(
                buildings__in=buildings
            ).distinct()
            
            if not developers.exists():
                return Response(
                    {"message": "No developers found under this maintenance company."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serialized_data = DeveloperProfileSerializer(developers, many=True)
            return Response(serialized_data.data, status=status.HTTP_200_OK)
        
        except MaintenanceCompanyProfile.DoesNotExist:
            return Response(
                {"error": f"Maintenance company with id {company_id} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DeveloperDetailUnderCompanyView(APIView):
    permission_classes = [AllowAny]  # Adjust this based on your permission needs

    def get(self, request, company_id, developer_id):
        try:
            # Step 1: Retrieve the maintenance company by its ID
            company = MaintenanceCompanyProfile.objects.get(id=company_id)
            
            # Step 2: Retrieve the elevators linked to the given maintenance company
            elevators = Elevator.objects.filter(maintenance_company=company)
            
            # Step 3: Get the buildings associated with these elevators
            buildings = set([elevator.building for elevator in elevators])
            
            # Step 4: Check if the developer is linked to any of these buildings
            developer = DeveloperProfile.objects.get(id=developer_id)
            developer_buildings = set([building for building in buildings if building.developer == developer])
            
            if not developer_buildings:
                # If no buildings are found for the specified developer, return an error
                return Response(
                    {"error": "Developer not found or not linked to any buildings under the specified maintenance company."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 5: Serialize the developer data
            serialized_data = DeveloperDetailSerializer(developer)

            # Step 6: Return the serialized developer data
            return Response(serialized_data.data, status=status.HTTP_200_OK)

        except MaintenanceCompanyProfile.DoesNotExist:
            # If the maintenance company doesn't exist
            return Response(
                {"error": "Maintenance company not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except DeveloperProfile.DoesNotExist:
            # If the developer doesn't exist
            return Response(
                {"error": "Developer not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log the exception details for debugging
            logger.error(f"Unexpected error: {str(e)}")
            # Handle any unexpected errors
            return Response(
                {"error": "An unexpected error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class BuildingsUnderDeveloperView(APIView):
    permission_classes = [AllowAny]
    serializer_class = BuildingSerializer

    def validate_uuid(self, uuid_string, param_name):
        """Validate UUID format"""
        if not isinstance(uuid_string, str):
            raise ValidationError(f"Invalid UUID format for {param_name}")
        try:
            uuid.UUID(uuid_string)
            return uuid_string
        except (ValueError, AttributeError, TypeError):
            raise ValidationError(f"Invalid UUID format for {param_name}")

    def get_maintenance_company(self, company_id):
        """Get maintenance company or raise 404"""
        try:
            logger.info(f"Retrieving maintenance company with ID: {company_id}")
            company = MaintenanceCompanyProfile.objects.get(id=company_id)
            logger.info(f"Found company: {company}")
            return company
        except MaintenanceCompanyProfile.DoesNotExist:
            logger.error(f"Maintenance company not found for ID: {company_id}")
            raise NotFound("Maintenance company not found.")

    def get_developer(self, developer_id):
        """Get developer or raise 404"""
        try:
            logger.info(f"Retrieving developer with ID: {developer_id}")
            developer = DeveloperProfile.objects.get(id=developer_id)
            logger.info(f"Found developer: {developer}")
            return developer
        except DeveloperProfile.DoesNotExist:
            logger.error(f"Developer not found for ID: {developer_id}")
            raise NotFound("Developer not found.")

    def get_buildings(self, developer, company):
        """Get buildings for developer and company"""
        logger.info(f"Retrieving buildings for developer {developer.id} and company {company.id}")
        elevators = Elevator.objects.filter(
            building__developer=developer,
            maintenance_company=company
        )
        
        if not elevators.exists():
            logger.warning("No buildings found")
            # Return consistent message format
            return Response(
                {"message": "No buildings found."},
                status=status.HTTP_404_NOT_FOUND
            )
            
        buildings = list({elevator.building for elevator in elevators})
        logger.info(f"Found {len(buildings)} buildings")
        return buildings

    def get(self, request, company_id, developer_id):
        """Get buildings associated with a developer and maintenance company"""
        try:
            # Validate UUIDs first
            try:
                valid_company_id = self.validate_uuid(company_id, "company_id")
                valid_developer_id = self.validate_uuid(developer_id, "developer_id")
            except ValidationError as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get required objects
            company = self.get_maintenance_company(valid_company_id)
            developer = self.get_developer(valid_developer_id)
            
            # Get buildings - this might return a Response for no buildings
            buildings = self.get_buildings(developer, company)
            if isinstance(buildings, Response):
                return buildings

            # Serialize and return data
            serialized_data = self.serializer_class(buildings, many=True)
            return Response(serialized_data.data)

        except NotFound as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ElevatorsUnderCompanyView(APIView):
    permission_classes = [AllowAny]  # Adjust as necessary for authentication and authorization

    def get(self, request, company_id):
        # company_id is already a UUID, so no need to convert it again
        # If necessary, you can validate if it's a valid UUID explicitly with:
        if not isinstance(company_id, UUID):
            return Response(
                {"error": "Invalid company ID format. Please provide a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fetch the maintenance company profile; returns 404 if not found
        company = get_object_or_404(MaintenanceCompanyProfile, id=company_id)

        # Fetch elevators linked to this maintenance company
        elevators = Elevator.objects.filter(maintenance_company=company)

        # Check if any elevators are found
        if not elevators.exists():
            return Response(
                {"message": "No elevators found for this building under the specified maintenance company."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Serialize and return the data
        serialized_data = ElevatorSerializer(elevators, many=True)
        return Response(serialized_data.data, status=status.HTTP_200_OK)

class ElevatorsInBuildingView(APIView):
    permission_classes = [AllowAny]  # Adjust based on your permission needs

    def get(self, request, company_id, building_id):
        # Step 1: Validate UUIDs
        if not self.is_valid_uuid(company_id) or not self.is_valid_uuid(building_id):
            return Response({"error": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Step 2: Retrieve the maintenance company
            company = MaintenanceCompanyProfile.objects.get(id=company_id)

            # Step 3: Retrieve the building
            building = Building.objects.get(id=building_id)

            # Step 4: Fetch elevators for the specified building
            elevators = Elevator.objects.filter(building=building)

            # Step 5: Check if elevators are found, if not raise a NotFound exception
            if not elevators.exists():
                raise NotFound(detail="No elevators found for this building under the specified maintenance company.", code=404)

            # Step 6: Serialize the elevator data
            serialized_data = ElevatorSerializer(elevators, many=True)

            return Response(serialized_data.data, status=status.HTTP_200_OK)

        except MaintenanceCompanyProfile.DoesNotExist:
            return Response({"error": "Maintenance company not found."}, status=status.HTTP_404_NOT_FOUND)

        except Building.DoesNotExist:
            return Response({"error": "Building not found."}, status=status.HTTP_404_NOT_FOUND)

        except NotFound as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}. Please try again later."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def is_valid_uuid(self, uuid_str):
        """Helper method to validate UUID format."""
        try:
            # If uuid_str is already a UUID object, just pass it
            if isinstance(uuid_str, uuid.UUID):
                return True
            uuid.UUID(str(uuid_str))  # We use str() in case it's already a UUID object
            return True
        except ValueError:
            return False

class ElevatorDetailView(APIView):
    permission_class = [AllowAny]

    def get(self, request, company_id, elevator_id):
        print("\n=== START OF REQUEST ===")
        print(f"URL Path: {request.path}")
        print(f"Company ID: {company_id}")
        print(f"Elevator ID: {elevator_id}")

        try:
            # Retrieve the maintenance company
            company = MaintenanceCompanyProfile.objects.get(id=company_id)
            print(f"Company found: {company.company_name}")

            # Retrieve the elevator
            elevator = Elevator.objects.get(id=elevator_id, maintenance_company=company)
            print(f"Elevator Found: {elevator.user_name} | Building: {elevator.building}")

            # Serialize the elevator data
            serializer = ElevatorReadSerializer(elevator)
            print("Serialization successful")
            serialized_data = serializer.data
            print("Data access successful")

            return Response(serialized_data, status=status.HTTP_200_OK)

        except MaintenanceCompanyProfile.DoesNotExist:
            print("Maintenance company not found.")
            return Response(
                {"error": "Maintenance company not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Elevator.DoesNotExist:
            print("Elevator not found.")
            return Response(
                {"error": "Elevator not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ElevatorDetailByMachineNumberView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, company_id, machine_number):
        """
        Retrieve elevator details by machine number and maintenance company.
        """
        # Validate machine number
        if not machine_number or not str(machine_number).strip():
            return Response(
                {"error": "Machine number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        print(f"Received company_id: {company_id} (string), machine_number: {machine_number}")
        
        # Validate machine number is numeric
        if not str(machine_number).strip().isdigit():
            return Response(
                {"error": "Machine number must be numeric"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            company = MaintenanceCompanyProfile.objects.get(id=company_id)
            elevator = Elevator.objects.get(
                machine_number=machine_number.strip(),
                maintenance_company=company
            )
            serialized_data = ElevatorSerializer(elevator)
            return Response(serialized_data.data)
            
        except MaintenanceCompanyProfile.DoesNotExist:
            return Response(
                {"error": "Maintenance company profile not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Elevator.DoesNotExist:
            return Response(
                {"error": "Elevator with the specified machine number not found under this maintenance company."},
                status=status.HTTP_404_NOT_FOUND
            )


class ElevatorDetailNoMachineView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, company_id):
        """
        Handle requests without machine number.
        Always returns 400 Bad Request.
        """
        return Response(
            {"error": "Machine number is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

class AddElevatorToBuildingView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ElevatorCreateSerializer,
        operation_description="Add a new elevator to a building with details.",
        responses={
            201: openapi.Response(
                description="Elevator created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                        'user_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'machine_number': openapi.Schema(type=openapi.TYPE_STRING),
                        'capacity': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'manufacturer': openapi.Schema(type=openapi.TYPE_STRING),
                        'installation_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'building': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                        'technician': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, nullable=True),
                    }
                )
            ),
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error"
        }
    )
    def put(self, request, company_uuid, building_uuid):
        try:
            # Print the building_uuid being passed
            print(f"Building UUID being passed: {building_uuid}")

            # Retrieve the building
            try:
                building = Building.objects.get(id=building_uuid)
            except Building.DoesNotExist:
                raise Http404("Building not found")

            # Check if technician UUID is valid (if provided)
            if 'technician' in request.data:
                try:
                    technician_uuid = UUID(str(request.data['technician']))
                except ValueError:
                    return Response(
                        {"technician": ["Value must be a valid UUID"]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                technician_uuid = None

            # Prepare elevator data with building_uuid
            elevator_data = request.data.copy()
            elevator_data['building'] = building_uuid

            # Pass the technician_uuid into the data dictionary
            if technician_uuid:
                elevator_data['technician'] = technician_uuid

            # Serialize and validate elevator data
            serializer = ElevatorCreateSerializer(data=elevator_data)
            if serializer.is_valid():
                elevator = serializer.save()
                return Response(
                    {
                        "id": str(elevator.id),
                        "user_name": elevator.user_name,
                        "machine_number": elevator.machine_number,
                        "capacity": elevator.capacity,
                        "manufacturer": elevator.manufacturer,
                        "installation_date": elevator.installation_date.isoformat(),
                        "building": str(elevator.building.id),
                        "technician": str(elevator.technician.id) if elevator.technician else None,
                        "controller_type": elevator.controller_type,
                        "machine_type": elevator.machine_type
                    },
                    status=status.HTTP_201_CREATED
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Http404 as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ElevatorsUnderTechnicianView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, company_id, technician_id):
        try:
            # Retrieve maintenance company by ID
            company = MaintenanceCompanyProfile.objects.get(id=company_id)

            # Retrieve technician by technician_id
            technician = TechnicianProfile.objects.get(id=technician_id)

            # Get elevators under this technician and maintenance company
            elevators = Elevator.objects.filter(
                maintenance_company=company,
                technician=technician
            )

            if not elevators.exists():
                return Response(
                    {"message": "No elevators found under this technician for the specified maintenance company."},
                    status=status.HTTP_404_NOT_FOUND
                )

            serialized_data = ElevatorSerializer(elevators, many=True)
            return Response(serialized_data.data, status=status.HTTP_200_OK)

        except MaintenanceCompanyProfile.DoesNotExist:
            return Response(
                {"error": "Maintenance company not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except TechnicianProfile.DoesNotExist:
            return Response(
                {"error": "Technician not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},  # Return error message from the exception
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class BuildingsUnderTechnicianView(APIView):
    permission_classes = [AllowAny]  # Adjust based on your permission needs

    def get(self, request, company_id, technician_id):
        try:
            # Step 1: Ensure the company_id and technician_id are in string format for processing
            company_id = str(company_id)  # Ensure company_id is a string
            technician_id = str(technician_id)  # Ensure technician_id is a string

            # Step 2: Retrieve the maintenance company by its ID
            try:
                company = MaintenanceCompanyProfile.objects.get(id=company_id)
            except MaintenanceCompanyProfile.DoesNotExist:
                return Response(
                    {"error": "Maintenance company not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 3: Retrieve the technician by technician_id
            try:
                technician = TechnicianProfile.objects.get(id=technician_id)
            except TechnicianProfile.DoesNotExist:
                return Response(
                    {"error": "Technician not found."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 4: Get all elevators under this maintenance company and technician
            elevators = Elevator.objects.filter(
                maintenance_company=company,
                technician=technician
            )

            # If no elevators are found, return an error message
            if not elevators.exists():
                return Response(
                    {"message": "No elevators found under this technician for the specified maintenance company."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 5: Get the buildings associated with the elevators
            buildings = Building.objects.filter(id__in=[elevator.building.id for elevator in elevators])

            # Step 6: Serialize the buildings data
            # Assuming you have a BuildingSerializer class
            serialized_data = BuildingSerializer(buildings, many=True)

            # Return the serialized data as a response
            return Response(serialized_data.data, status=status.HTTP_200_OK)

        except Exception as e:
            # Catch any unexpected errors and return them in the response
            return Response(
                {"error": f"An unexpected error occurred. Details: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class TechnicianDetailForCompanyView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get technician details",
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer <>",  # Updated this
                type=openapi.TYPE_STRING
            )
        ],
        responses={
            200: openapi.Response('Successful response'),
            401: 'Unauthorized',
            403: 'Forbidden'
        }
    ) 
    def get(self, request, company_uuid, technician_uuid):
        try:
            company = MaintenanceCompanyProfile.objects.get(id=company_uuid)
            
            # Check if the current user is the owner of the company
            if company.user != request.user:
                raise PermissionDenied("You do not have permission to view this technician's details")
                
            technician = TechnicianProfile.objects.get(id=technician_uuid, maintenance_company=company)
            
            data = {
                "id": str(technician.id),
                "technician_name": f"{technician.user.first_name} {technician.user.last_name}",
                "specialization": technician.specialization,
                "maintenance_company_name": company.company_name,
                "email": technician.user.email,
                "phone_number": technician.user.phone_number,
            }
            return Response(data, status=status.HTTP_200_OK)
            
        except MaintenanceCompanyProfile.DoesNotExist:
            return Response({"detail": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        except TechnicianProfile.DoesNotExist:
            return Response({"detail": "Technician not found"}, status=status.HTTP_404_NOT_FOUND)

    def handle_exception(self, exc):
        """
        Handle exceptions that occur during request processing
        """
        if isinstance(exc, NotAuthenticated):
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return super().handle_exception(exc)


class UpdateTechnicianOnBuildingsView(APIView):
    permission_classes = [AllowAny]  # Adjust based on your needs (authentication, etc.)

    @swagger_auto_schema(
        operation_description="Update technician for all elevators in a building",
        manual_parameters=[
            openapi.Parameter(
                'company_uuid',
                openapi.IN_PATH,
                description="UUID of the maintenance company",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True
            ),
            openapi.Parameter(
                'building_uuid',
                openapi.IN_PATH,
                description="UUID of the building",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['technician_id'],
            properties={
                'technician_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_UUID,
                    description="UUID of the technician to assign"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Successfully updated technician",
                examples={
                    "application/json": [{
                        "id": "uuid",
                        "user_name": "example",
                        "technician": {
                            "id": "uuid",
                            "name": "John Doe"
                        },
                        "capacity": "1000kg",
                        "building": {
                            "id": "uuid",
                            "name": "Building Name"
                        }
                    }]
                }
            ),
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error"
        }
    )
    def put(self, request, company_uuid, building_uuid):
        try:
            # Step 1: Validate and retrieve the Maintenance Company
            self.validate_uuid(company_uuid)
            company = MaintenanceCompanyProfile.objects.get(id=company_uuid)

            # Step 2: Validate and retrieve the Building
            self.validate_uuid(building_uuid)
            building = Building.objects.get(id=building_uuid)

            # Step 3: Check if elevators exist for the given building and maintenance company
            elevators = Elevator.objects.filter(building=building, maintenance_company=company)
            if not elevators.exists():
                return Response(
                    {"error": "No elevators found for this building under the specified maintenance company."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Step 4: Retrieve and validate the technician from the request data
            technician_id = request.data.get("technician_id", None)
            if not technician_id:
                return Response({"error": "Technician ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            self.validate_uuid(technician_id)
            technician = TechnicianProfile.objects.get(id=technician_id, maintenance_company=company)
            
            # Step 5: Update the technician for all elevators in the building
            elevators.update(technician=technician)

            # Step 6: Serialize and return the updated elevator data
            updated_elevators = Elevator.objects.filter(building=building, maintenance_company=company)
            elevator_data = [{
                "id": str(elevator.id),
                "user_name": elevator.user_name,
                "technician": {
                    "id": str(technician.id),
                    "name": f"{technician.user.first_name} {technician.user.last_name}"
                },
                "capacity": elevator.capacity,
                "building": {
                    "id": str(building.id),
                    "name": building.name
                }
            } for elevator in updated_elevators]

            return Response(elevator_data, status=status.HTTP_200_OK)

        except MaintenanceCompanyProfile.DoesNotExist:
            return Response({"error": "Maintenance company not found."}, status=status.HTTP_404_NOT_FOUND)
        except Building.DoesNotExist:
            return Response({"error": "Building not found."}, status=status.HTTP_404_NOT_FOUND)
        except TechnicianProfile.DoesNotExist:
            return Response({"error": "Technician not found or does not belong to this maintenance company."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}. Please try again later."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def validate_uuid(self, uuid_str):
        """Validate if the provided string is a valid UUID."""
        try:
            uuid_obj = uuid.UUID(str(uuid_str))
            return uuid_obj
        except ValueError:
            raise ValidationError(f"Invalid UUID format: {uuid_str}")

class UpdateTechnicianOnElevatorView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
       operation_description="Update technician for a specific elevator",
       manual_parameters=[
           openapi.Parameter(
               'company_uuid',
               openapi.IN_PATH,
               description="UUID of the maintenance company",
               type=openapi.TYPE_STRING,
               format=openapi.FORMAT_UUID,
               required=True
           ),
           openapi.Parameter(
               'elevator_uuid', 
               openapi.IN_PATH,
               description="UUID of the elevator",
               type=openapi.TYPE_STRING,
               format=openapi.FORMAT_UUID,
               required=True
           )
       ],
       request_body=openapi.Schema(
           type=openapi.TYPE_OBJECT,
           required=['technician_id'],
           properties={
               'technician_id': openapi.Schema(
                   type=openapi.TYPE_STRING, 
                   format=openapi.FORMAT_UUID,
                   description="UUID of the technician to assign"
               )
           }
       ),
       responses={
           200: ElevatorSerializer,
           400: "Bad Request - Technician ID is required",
           404: "Not Found - Company, Elevator or Technician not found"
       }
   )
    def put(self, request, company_uuid, elevator_uuid):
        # Retrieve the maintenance company by UUID
        company = get_object_or_404(MaintenanceCompanyProfile, id=company_uuid)

        # Retrieve the elevator by UUID, ensuring it belongs to the specified company
        elevator = get_object_or_404(Elevator, id=elevator_uuid, maintenance_company=company)
        
        # Get technician ID from the request body
        technician_id = request.data.get("technician_id")
        if not technician_id:
            return Response({"error": "Technician ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the technician by UUID, ensuring they belong to the specified company
        technician = get_object_or_404(TechnicianProfile, id=technician_id, maintenance_company=company)

        # Update the elevator with the technician
        elevator.technician = technician
        elevator.save()

        # Serialize the updated elevator object
        serializer = ElevatorSerializer(elevator)

        # Return the updated elevator data in the response
        return Response(serializer.data, status=status.HTTP_200_OK)

class RemoveMaintenanceFromBuildingElevatorsView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, company_id, building_id):
        try:
            # Ensure company_id is a valid UUID
            company_id = self.convert_to_uuid(company_id)
            maintenance_company = self.get_object(MaintenanceCompanyProfile, company_id)
            if not maintenance_company:
                return Response({"error": "Maintenance company not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Ensure building_id is a valid UUID
            building_id = self.convert_to_uuid(building_id)
            building = self.get_object(Building, building_id)
            if not building:
                return Response({"error": "Building not found."}, status=status.HTTP_404_NOT_FOUND)
            
            # Get all elevators linked to this building
            elevators = Elevator.objects.filter(building=building)

            # Get elevators that are linked to the maintenance company
            affected_elevators = elevators.filter(maintenance_company=maintenance_company)

            # Check if there are elevators linked to this maintenance company
            if not affected_elevators.exists():
                return Response(
                    {"message": "No elevators linked to the provided maintenance company in this building."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Step 1: Update MaintenanceSchedule for affected elevators
            affected_schedules = MaintenanceSchedule.objects.filter(
                elevator__in=affected_elevators,
                status__in=['scheduled', 'overdue']
            )
            affected_schedules_updated = affected_schedules.update(maintenance_company=None, technician=None)

            # Step 2: Update the elevators by removing the maintenance company
            affected_elevators_updated = affected_elevators.update(maintenance_company=None, technician=None)

            # Prepare the success response
            return Response(
                {
                    "message": f"Successfully removed the maintenance company and technician from {affected_elevators_updated} elevator(s) "
                               f"and {affected_schedules_updated} maintenance schedule(s)."
                },
                status=status.HTTP_200_OK
            )
        
        except DatabaseError as e:
            # Simulating an error like a database failure (for testing purposes)
            return Response({"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            # General error handling
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def convert_to_uuid(self, object_id):
        """
        Convert a string or UUID to a UUID object if necessary.
        """
        if isinstance(object_id, uuid.UUID):
            return object_id
        try:
            return uuid.UUID(object_id)
        except ValueError:
            raise ValueError(f"Invalid UUID format for {object_id}")

    def get_object(self, model, object_id):
        """
        Helper method to get an object by UUID and handle DoesNotExist exceptions.
        Returns the object if found, otherwise None.
        """
        try:
            return model.objects.get(id=object_id)
        except model.DoesNotExist:
            return None

class RemoveMaintenanceFromDeveloperElevatorsView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, company_id, developer_id):
        # Directly use company_id and developer_id as UUIDs without conversion
        
        # Retrieve the maintenance company
        maintenance_company = self.get_object(MaintenanceCompanyProfile, company_id)
        if not maintenance_company:
            return Response({"error": "Maintenance company not found."}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve the developer
        developer = self.get_object(DeveloperProfile, developer_id)
        if not developer:
            return Response({"error": "Developer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get all buildings linked to the developer
        buildings = Building.objects.filter(developer=developer)
        if not buildings.exists():
            return Response({"message": "No buildings found for this developer."}, status=status.HTTP_404_NOT_FOUND)

        # Get all elevators linked to these buildings
        elevators = Elevator.objects.filter(building__in=buildings)
        if not elevators.exists():
            return Response({"message": "No elevators found for this developer."}, status=status.HTTP_404_NOT_FOUND)

        # Get elevators linked to the maintenance company
        affected_elevators = elevators.filter(maintenance_company=maintenance_company)
        if not affected_elevators.exists():
            return Response({"message": "No elevators linked to the provided maintenance company for this developer."}, status=status.HTTP_404_NOT_FOUND)

        # Step 1: Update MaintenanceSchedule for affected elevators
        affected_schedules = MaintenanceSchedule.objects.filter(
            elevator__in=affected_elevators,
            status__in=['scheduled', 'overdue']
        )
        affected_schedules_count = affected_schedules.count()

        # Remove the maintenance company and technician from schedules
        affected_schedules.update(maintenance_company=None, technician=None)

        # Step 2: Update the elevators
        affected_elevators_count = affected_elevators.count()
        affected_elevators.update(maintenance_company=None, technician=None)

        # Prepare the success response
        return Response(
            {
                "message": f"Successfully removed the maintenance company and technician from {affected_elevators_count} elevator(s) "
                           f"and {affected_schedules_count} maintenance schedule(s)."
            },
            status=status.HTTP_200_OK
        )

    def get_object(self, model, object_id):
        """
        Helper method to get an object by UUID and handle DoesNotExist exceptions.
        Returns the object if found, otherwise returns None.
        """
        try:
            return model.objects.get(id=object_id)
        except ObjectDoesNotExist:
            return None
        except Exception as e:
            raise DatabaseError(f"Unexpected error occurred: {str(e)}")

