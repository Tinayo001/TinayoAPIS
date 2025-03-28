from django.http import Http404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from rest_framework.generics import RetrieveAPIView 
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import UpdateAPIView
from rest_framework.exceptions import NotFound
from rest_framework.generics import DestroyAPIView
from .models import Elevator
from buildings.models import Building
from .serializers import ElevatorSerializer
from .serializers import ElevatorCreateSerializer
import logging
import uuid
from rest_framework.permissions import IsAuthenticated
from .services.elevator_service import ElevatorService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .models import ElevatorIssueLog
from django.utils import timezone
from rest_framework.generics import ListAPIView

from .serializers import ElevatorIssueLogSerializer
from jobs.serializers import AdHocMaintenanceScheduleSerializer
from jobs.models import AdHocMaintenanceSchedule
from django.db.models import Q
from alerts.models import AlertType
from alerts.services import AlertService

logger = logging.getLogger(__name__)

class AddElevatorView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ElevatorCreateSerializer,
        operation_description="Add a new elevator with details.",
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
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to create a new elevator.
        """
        serializer = ElevatorCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                elevator = ElevatorService.create_elevator(serializer.validated_data)
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
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ElevatorListView(ListAPIView):
    """
    API view to list all elevators with pagination, filtering, and sorting.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed
    queryset = Elevator.objects.all()
    serializer_class = ElevatorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['building', 'machine_type', 'manufacturer']  # Add fields to filter by
    ordering_fields = ['installation_date', 'capacity']  # Add fields to sort by
    ordering = ['-installation_date']  # Default ordering

    @swagger_auto_schema(
        operation_description="Retrieve a list of all elevators with optional filtering and sorting.",
        manual_parameters=[
            openapi.Parameter(
                name='building',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by building UUID.",
            ),
            openapi.Parameter(
                name='machine_type',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by machine type (e.g., 'gearless', 'geared').",
            ),
            openapi.Parameter(
                name='manufacturer',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by manufacturer name.",
            ),
            openapi.Parameter(
                name='ordering',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Sort by fields (e.g., 'installation_date', '-capacity').",
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of elevators retrieved successfully.",
                schema=ElevatorSerializer(many=True),
            ),
            500: "Internal Server Error",
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ElevatorDetailByIdView(RetrieveAPIView):
    """
    Retrieve a specific elevator by its ID.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed
    queryset = Elevator.objects.all()
    serializer_class = ElevatorSerializer
    lookup_field = 'id'  # Match the URL keyword argument

    @swagger_auto_schema(
        operation_description="Retrieve a specific elevator by its ID.",
        responses={
            200: openapi.Response(
                description="Elevator retrieved successfully.",
                schema=ElevatorSerializer,
            ),
            404: "Elevator not found.",
            500: "Internal Server Error",
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve an elevator by its ID.
        """
        try:
            elevator_id = kwargs['id']
            logger.info(f"Attempting to retrieve elevator with ID: {elevator_id}")
            return super().get(request, *args, **kwargs)
        except Http404:
            logger.error(f"Elevator with ID {elevator_id} not found.")
            return Response(
                {"detail": "Elevator not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving elevator: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ElevatorDetailByMachineNumberView(RetrieveAPIView):
    """
    Retrieve a specific elevator by its machine number.
    """
    permission_classes = [AllowAny]  # Allow any user to access this endpoint
    serializer_class = ElevatorSerializer
    lookup_field = 'machine_number'  # Use machine_number for lookup

    def get_object(self):
        """
        Retrieve the elevator by its machine number.
        """
        machine_number = self.kwargs['machine_number']
        logger.info(f"Attempting to retrieve elevator with machine number: {machine_number}")
        return get_object_or_404(Elevator, machine_number=machine_number)

    @swagger_auto_schema(
        operation_description="Retrieve a specific elevator by its machine number.",
        responses={
            200: openapi.Response(
                description="Elevator retrieved successfully.",
                schema=ElevatorSerializer,
            ),
            404: "Elevator not found.",
            500: "Internal Server Error",
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve an elevator by its machine number.
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            logger.error(f"Elevator with machine number {self.kwargs['machine_number']} not found.")
            return Response(
                {"detail": "Elevator not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving elevator: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ElevatorsInBuildingView(APIView):
    """
    Get all elevators in a specific building identified by building_id.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    @swagger_auto_schema(
        operation_description="Retrieve all elevators in a specific building.",
        responses={
            200: openapi.Response(
                description="Elevators retrieved successfully.",
                schema=ElevatorSerializer(many=True),
            ),
            404: "Building not found or no elevators found for this building.",
        }
    )
    def get(self, request, building_id, *args, **kwargs):
        """
        Handle GET request to retrieve all elevators in a building.
        """
        try:
            # Retrieve the building by its UUID
            building = get_object_or_404(Building, id=building_id)
            logger.info(f"Retrieving elevators for building ID: {building_id}")

            # Get all elevators related to this building
            elevators = building.elevators.all()

            # Check if there are no elevators for the given building
            if not elevators.exists():
                logger.warning(f"No elevators found for building ID: {building_id}")
                return Response(
                    {"detail": "No elevators found for this building."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize the elevator data
            serializer = ElevatorSerializer(elevators, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404:
            logger.error(f"Building with ID {building_id} not found.")
            return Response(
                {"detail": "Building not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving elevators for building ID {building_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class DeleteElevatorView(DestroyAPIView):
    """
    Delete a specific elevator by its ID.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed
    queryset = Elevator.objects.all()
    serializer_class = ElevatorSerializer
    lookup_field = 'id'  # Use 'id' as the lookup field

    @swagger_auto_schema(
        operation_description="Delete a specific elevator by its ID.",
        responses={
            204: openapi.Response(
                description="Elevator deleted successfully.",
            ),
            404: "Elevator not found.",
            500: "Internal Server Error",
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete an elevator by its ID.
        """
        try:
            elevator_id = self.kwargs['id']
            logger.info(f"Attempting to delete elevator with ID: {elevator_id}")
            return super().delete(request, *args, **kwargs)
        except Http404:
            logger.error(f"Elevator with ID {elevator_id} not found.")
            return Response(
                {"detail": "Elevator not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting elevator with ID {elevator_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogElevatorIssueView(APIView):
    """
    Log an issue for a specific elevator and notify relevant parties.
    If an urgency message is provided, a maintenance schedule will be created.
    """
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Log an issue for a specific elevator. If an 'Urgency' message is provided, an ad-hoc maintenance schedule is created.",
        manual_parameters=[
            openapi.Parameter(
                'elevator_id',
                openapi.IN_PATH,
                description="UUID of the elevator",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True
            ),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['issue_description'],
            properties={
                'issue_description': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Detailed description of the elevator issue",
                    example="The elevator is stuck between floors."
                ),
                'Urgency': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Specify if urgent action is required",
                    example="Technician needed urgently"
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Issue logged successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "issue_id": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                        "maintenance_schedule_id": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                        "alerts": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING))
                    }
                )
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def put(self, request, elevator_id, *args, **kwargs):
        # Validate elevator ID
        try:
            elevator_uuid = uuid.UUID(str(elevator_id))
        except ValueError:
            return Response({"detail": "Invalid elevator ID format. Must be a valid UUID."}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Fetch elevator
        try:
            elevator = Elevator.objects.get(id=elevator_uuid)
        except Elevator.DoesNotExist:
            return Response({"detail": "Elevator not found."}, 
                          status=status.HTTP_404_NOT_FOUND)

        # Extract issue description
        issue_description = request.data.get('issue_description')
        if not issue_description:
            return Response({"detail": "Issue description is required."}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Create ElevatorIssueLog entry
        issue_log = ElevatorIssueLog.objects.create(
            elevator=elevator,
            developer=elevator.developer,
            building=elevator.building,
            issue_description=issue_description
        )

        created_alerts = []
        maintenance_schedule_id = None

        try:
            # Create alert for technician if assigned
            if elevator.technician:
                tech_alert = AlertService.create_alert(
                    alert_type=AlertType.LOG_ADDED,
                    recipient=elevator.technician,
                    related_object=issue_log,
                    message=f"New issue reported for elevator {elevator.machine_number} "
                           f"in building {elevator.building.name}: {issue_description}"
                )
                created_alerts.append(str(tech_alert.id))

            # Create alert for maintenance company
            if elevator.maintenance_company:
                company_alert = AlertService.create_alert(
                    alert_type=AlertType.LOG_ADDED,
                    recipient=elevator.maintenance_company,
                    related_object=issue_log,
                    message=f"New issue reported for elevator {elevator.machine_number} "
                           f"in building {elevator.building.name}: {issue_description}"
                )
                created_alerts.append(str(company_alert.id))

            # Handle urgency message and create an ad-hoc maintenance schedule
            urgency_message = request.data.get('Urgency')
            if urgency_message:
                if not elevator.technician:
                    return Response(
                        {"detail": "No technician assigned to this elevator. Cannot create maintenance schedule."}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

                maintenance_description = (
                    f"Urgent maintenance needed: {issue_description}\n"
                    f"Reported on: {timezone.now().date()}"
                )

                # Create maintenance schedule
                schedule = AdHocMaintenanceSchedule.objects.create(
                    elevator=elevator,
                    maintenance_company=elevator.maintenance_company,
                    technician=elevator.technician,
                    scheduled_date=timezone.now(),
                    description=maintenance_description
                )
                maintenance_schedule_id = str(schedule.id)

                # Create alert for ad-hoc maintenance schedule
                schedule_alert = AlertService.create_alert(
                    alert_type=AlertType.ADHOC_MAINTENANCE_SCHEDULED,
                    recipient=elevator.technician,
                    related_object=schedule,
                    message=f"Urgent maintenance schedule created for elevator "
                           f"{elevator.machine_number} in building {elevator.building.name}"
                )
                created_alerts.append(str(schedule_alert.id))

        except Exception as e:
            return Response(
                {"detail": f"Error creating alerts: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response_data = {
            "message": "Issue logged successfully.",
            "issue_id": str(issue_log.id),
            "alerts": created_alerts
        }

        if maintenance_schedule_id:
            response_data.update({
                "message": "Issue logged and ad-hoc maintenance schedule created successfully.",
                "maintenance_schedule_id": maintenance_schedule_id
            })

        return Response(response_data, status=status.HTTP_201_CREATED)

class LoggedElevatorIssuesView(APIView):
    """
    List all the logged issues for a specific elevator.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get(self, request, elevator_id, *args, **kwargs):
        """
        Get a list of all issues logged for a specific elevator.
        """
        # Retrieve the elevator by UUID
        elevator = get_object_or_404(Elevator, id=elevator_id)

        # Get all logged issues for this elevator
        issues = ElevatorIssueLog.objects.filter(elevator=elevator)

        # If no issues are found, return a message
        if not issues.exists():
            return Response({"detail": "No issues logged for this elevator."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the issues data
        serializer = ElevatorIssueLogSerializer(issues, many=True)

        # Return the list of logged issues
        return Response(serializer.data, status=status.HTTP_200_OK)

class ElevatorWithRunningSchedulesView(APIView):
    permission_classes = [AllowAny]  # Adjust permission as necessary

    def get(self, request, *args, **kwargs):
        """
        List all elevators that have a running scheduled maintenance for today or in the future.
        """
        # We need to filter elevators that have a maintenance schedule with a scheduled date today or in the future
        elevators_with_schedules = Elevator.objects.filter(
            maintenance_schedules__scheduled_date__gte=timezone.now().date(),  # Include today or future dates
            maintenance_schedules__status="scheduled"  # Only include scheduled maintenance
        ).distinct()  # Remove duplicate entries for the same elevator

        # Serialize the elevator data
        serializer = ElevatorSerializer(elevators_with_schedules, many=True)

        # Return the serialized data in the response
        return Response(serializer.data, status=status.HTTP_200_OK)

class ElevatorWithoutRunningSchedulesView(APIView):
    permission_classes = [AllowAny]  # Adjust permission as necessary

    def get(self, request, *args, **kwargs):
        # Get today's date
        today = timezone.now().date()

        # Find all elevators that do not have maintenance schedules scheduled for today or in the future
        elevators_without_schedules = Elevator.objects.filter(
            ~Q(maintenance_schedules__scheduled_date__gte=today)
        ).distinct()

        # If no elevators are found, return 404 not found
        if not elevators_without_schedules:
            raise NotFound(detail="No elevators without running schedules found.")

        # Serialize the elevator data using ElevatorSerializer
        serializer = ElevatorSerializer(elevators_without_schedules, many=True)

        # Return the serialized data in the response
        return Response(serializer.data, status=status.HTTP_200_OK)
