from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import IsAuthenticated
from dateutil import parser
from drf_spectacular.types import OpenApiTypes
from uuid import UUID
from rest_framework import status
from rest_framework.response import Response
from django.http import HttpRequest
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.parsers import JSONParser
from .utils import get_next_scheduled_date
from .utils import update_schedule_status_and_create_new_schedule
from .models import *
from .serializers import *
from .serializers import MaintenanceScheduleSerializer, AdhocScheduleCreateSerializer, BuildingScheduleCompletionSerializer
from .serializers import FullMaintenanceScheduleSerializer
from elevators.models import Elevator
from technicians.models import TechnicianProfile
from developers.models import DeveloperProfile
from buildings.models import Building
from maintenance_companies.models import MaintenanceCompanyProfile
from datetime import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404

from django.db.models.query import QuerySet
from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from typing import List, Union, Optional
from .exceptions import InvalidFilterError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from alerts.services import AlertService
from alerts.models import AlertType

import logging

logger = logging.getLogger(__name__)


class CreateRoutineMaintenanceScheduleView(APIView):
   permission_classes = [AllowAny]

   @swagger_auto_schema(
       operation_description="Create a maintenance schedule for a specific elevator",
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
           required=['next_schedule', 'scheduled_date', 'description'],
           properties={
               'next_schedule': openapi.Schema(
                   type=openapi.TYPE_STRING,
                   enum=['1_month', '3_months', '6_months', 'set_date'],
                   description="Frequency of the next maintenance schedule"
               ),
               'scheduled_date': openapi.Schema(
                   type=openapi.TYPE_STRING,
                   description="Scheduled date in YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ format"
               ),
               'description': openapi.Schema(
                   type=openapi.TYPE_STRING,
                   description="Description of the maintenance schedule"
               )
           }
       ),
       responses={
           201: "Maintenance schedule created successfully",
           400: "Bad Request - Invalid input data",
           404: "Not Found - Elevator does not exist",
           409: "Conflict - Active maintenance schedule already exists"
       }
   )
   def post(self, request, elevator_id):
       try:
           logger.info(f"Creating maintenance schedule for elevator {elevator_id}")
           
           try:
               elevator_uuid = UUID(str(elevator_id))
           except ValueError:
               logger.error(f"Invalid elevator UUID format: {elevator_id}")
               return Response(
                   {"detail": "Invalid elevator ID format"},
                   status=status.HTTP_404_NOT_FOUND
               )

           try:
               elevator = Elevator.objects.get(id=elevator_uuid)
           except Elevator.DoesNotExist:
               logger.error(f"Elevator not found: {elevator_id}")
               return Response(
                   {"detail": "Elevator not found"},
                   status=status.HTTP_404_NOT_FOUND
               )

           required_fields = ['next_schedule', 'scheduled_date', 'description']
           if not all(field in request.data for field in required_fields):
               missing_fields = [field for field in required_fields if field not in request.data]
               logger.error(f"Missing required fields: {missing_fields}")
               return Response(
                   {"detail": f"Missing required fields: {', '.join(missing_fields)}"},
                   status=status.HTTP_400_BAD_REQUEST
               )

           if request.data['next_schedule'] != 'set_date':
               existing_schedule = MaintenanceSchedule.objects.filter(
                   elevator=elevator,
                   next_schedule=request.data['next_schedule'],
                   status__in=['scheduled', 'overdue']
               ).exists()

               if existing_schedule:
                   logger.warning(f"Existing active schedule found for elevator {elevator_id}")
                   return Response(
                       {"detail": "An active maintenance schedule already exists for this elevator"},
                       status=status.HTTP_409_CONFLICT
                   )

           try:
               date_str = request.data['scheduled_date']
               
               try:
                   if 'T' in date_str:
                       scheduled_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                   else:
                       scheduled_date = datetime.strptime(date_str, '%Y-%m-%d')
                       scheduled_date = scheduled_date.replace(hour=23, minute=59, second=59)
               
                   scheduled_date = timezone.make_aware(scheduled_date)
                   
               except ValueError:
                   logger.error(f"Invalid date format provided: {date_str}")
                   return Response(
                       {"detail": "Invalid date format. Please provide a valid date in the format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ'."},
                       status=status.HTTP_400_BAD_REQUEST
                   )

               current_date = timezone.now()
               if scheduled_date < current_date:
                   logger.warning(f"Attempted to schedule maintenance in the past: {scheduled_date}")
                   return Response(
                       {"detail": "Scheduled date cannot be in the past."},
                       status=status.HTTP_400_BAD_REQUEST
                   )

           except ValueError as e:
               logger.error(f"Date validation error: {str(e)}")
               return Response(
                   {"detail": "Invalid date format. Please provide a valid date in the format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ'."},
                   status=status.HTTP_400_BAD_REQUEST
               )

           schedule_data = {
               **request.data,
               'elevator': str(elevator.id),
               'technician': str(elevator.technician.id) if elevator.technician else None,
               'maintenance_company': str(elevator.maintenance_company.id) if elevator.maintenance_company else None,
               'scheduled_date': scheduled_date,
               'status': 'scheduled'
           }

           serializer = MaintenanceScheduleSerializer(data=schedule_data)
           
           if serializer.is_valid():
               schedule = serializer.save()
               
               logger.info(
                   f"Maintenance schedule created - ID: {schedule.id}, "
                   f"Status: scheduled, "
                   f"Scheduled Date: {scheduled_date}, "
                   f"Current Date: {current_date}"
               )

               if elevator.technician:
                   schedule_type = request.data['next_schedule'].replace('_', ' ').title()
                   
                   AlertService.create_alert(
                       alert_type=AlertType.SCHEDULE_ASSIGNED,
                       recipient=elevator.technician,
                       related_object=schedule,
                       message=(
                           f"New {schedule_type} maintenance schedule assigned for elevator {elevator.machine_number}. "
                           f"Scheduled for: {scheduled_date.strftime('%Y-%m-%d %H:%M')}"
                       )
                   )

               return Response(
                   {
                       "message": "Maintenance schedule created successfully",
                       "maintenance_schedule_id": str(schedule.id),
                       "elevator_id": str(elevator.id),
                       "technician_id": str(elevator.technician.id) if elevator.technician else None,
                       "maintenance_company_id": str(elevator.maintenance_company.id) if elevator.maintenance_company else None,
                       "status": 'scheduled',
                       "scheduled_date": scheduled_date.isoformat(),
                       "created_at": timezone.now().isoformat()
                   },
                   status=status.HTTP_201_CREATED
               )
           
           logger.error(f"Serializer validation failed: {serializer.errors}")
           return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

       except Exception as e:
           logger.error(f"Error creating maintenance schedule: {str(e)}", exc_info=True)
           return Response(
               {"detail": f"An error occurred while creating the maintenance schedule: {str(e)}"},
               status=status.HTTP_400_BAD_REQUEST
           )

class CreateAdHocMaintenanceScheduleView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Create an ad-hoc maintenance schedule for a given elevator UUID. "
                            "Technician and maintenance company are auto-assigned based on the elevator.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'scheduled_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_DATETIME,
                    description="Scheduled date for the maintenance (ISO 8601 format)."
                ),
                'description': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Description of the maintenance task."
                ),
            },
            required=['scheduled_date', 'description']
        ),
        responses={
            201: openapi.Response(
                description="Ad-hoc maintenance schedule created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Success message."),
                        'maintenance_schedule_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID of the created maintenance schedule."),
                        'schedule': openapi.Schema(type=openapi.TYPE_OBJECT, description="The created schedule details.")
                    }
                )
            ),
            400: openapi.Response(
                description="Bad request - missing or invalid parameters",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING, description="Error message.")
                    }
                )
            ),
        }
    )
    def post(self, request, elevator_uuid):
        try:
            # Get the elevator instance by UUID
            elevator = get_object_or_404(Elevator, id=elevator_uuid)

            # Extract and validate the request data
            description = request.data.get("description")
            scheduled_date = request.data.get("scheduled_date")

            # Handle missing description
            if not description:
                return Response(
                    {"detail": "Missing required field: description."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Handle missing scheduled_date
            if not scheduled_date:
                return Response(
                    {"detail": "Missing required field: scheduled_date."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Try parsing the scheduled_date with dateutil.parser.parse
            try:
                # Try parsing the scheduled date string
                scheduled_datetime = parser.isoparse(scheduled_date)
            except ValueError:
                # If parsing fails, assume it's just a date without time
                try:
                    scheduled_datetime = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
                    # Automatically set the time to midnight (00:00:00)
                    scheduled_datetime = datetime.combine(scheduled_datetime, datetime.min.time())
                except ValueError:
                    # Log the error for debugging
                    print(f"Error parsing date: {scheduled_date}")
                    return Response(
                        {"detail": "Invalid date format. Please provide a valid date in the format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SS'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Check if scheduled_datetime is naive (no timezone info) before making it aware
            if timezone.is_naive(scheduled_datetime):
                scheduled_datetime = timezone.make_aware(scheduled_datetime, timezone.get_current_timezone())

            # Ensure the scheduled date is in the future
            if scheduled_datetime < timezone.now():
                return Response(
                    {"detail": "The scheduled date cannot be in the past. Please choose a future date."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the Ad-Hoc Maintenance Schedule
            maintenance_schedule = AdHocMaintenanceSchedule.objects.create(
                elevator=elevator,
                description=description,
                scheduled_date=scheduled_datetime,
                technician=elevator.technician,  # Assign technician from the elevator
                maintenance_company=elevator.maintenance_company  # Assign maintenance company from the elevator
            )

            # Create alert for the technician
            if elevator.technician:
                AlertService.create_alert(
                    alert_type=AlertType.ADHOC_MAINTENANCE_SCHEDULED,
                    recipient=elevator.technician,
                    related_object=maintenance_schedule,
                    message=f"New ad-hoc maintenance scheduled for elevator {elevator.machine_number} on {scheduled_datetime.strftime('%Y-%m-%d %H:%M')}"
                )

            # Serialize the maintenance schedule and return a response
            serializer = AdHocMaintenanceScheduleSerializer(maintenance_schedule)
            return Response(
                {
                    "message": "Ad-Hoc maintenance schedule created successfully",
                    "maintenance_schedule_id": maintenance_schedule.id,
                    "schedule": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            return Response(
                {"detail": f"An error occurred while creating the maintenance schedule: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

class ChangeMaintenanceScheduleToCompletedView(APIView):
    permission_classes = [IsAuthenticated]
    
    def put(self, request, schedule_id):
        """
        Mark a maintenance schedule as completed and generate the next schedule if applicable.
        """
        maintenance_schedule = get_object_or_404(MaintenanceSchedule, id=schedule_id)
        
        # Check if the technician is assigned
        if maintenance_schedule.technician is None:
            return Response(
                {"detail": "This maintenance schedule cannot be completed as no technician has been assigned."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if schedule is overdue and send alerts if needed
        self._check_and_handle_overdue_status(maintenance_schedule)

        # Status transition handlers
        status_transitions = {
            'completed': self._handle_already_completed,
            'overdue': self._handle_overdue_status,
            'scheduled': self._handle_scheduled_status,
        }
        
        handler = status_transitions.get(maintenance_schedule.status)
        if handler:
            return handler(maintenance_schedule)
        
        return Response(
            {"detail": "Unexpected status."},
            status=status.HTTP_400_BAD_REQUEST
        )

    def _generate_next_schedule(self, maintenance_schedule):
        """
        Generate the next maintenance schedule based on the frequency.
        Returns None for one-time schedules or if generation fails.
        """
        if maintenance_schedule.next_schedule == 'set_date':
            return None  # Don't generate next schedule for one-time schedules

        schedule_intervals = {
            '1_month': relativedelta(months=1),
            '3_months': relativedelta(months=3),
            '6_months': relativedelta(months=6),
        }

        interval = schedule_intervals.get(maintenance_schedule.next_schedule)
        if not interval:
            return None

        next_date = maintenance_schedule.scheduled_date + interval
        
        # Check if a schedule already exists for this elevator on the calculated date
        existing_schedule = MaintenanceSchedule.objects.filter(
            elevator=maintenance_schedule.elevator,
            scheduled_date=next_date
        ).first()
        
        if existing_schedule:
            return existing_schedule

        try:
            new_schedule = MaintenanceSchedule.objects.create(
                elevator=maintenance_schedule.elevator,
                technician=maintenance_schedule.technician,
                maintenance_company=maintenance_schedule.maintenance_company,
                scheduled_date=next_date,
                next_schedule=maintenance_schedule.next_schedule,
                description=f"Routine {maintenance_schedule.next_schedule.replace('_', ' ')} maintenance",
                status='scheduled'
            )

            if new_schedule.technician:
                AlertService.create_alert(
                    alert_type=AlertType.SCHEDULE_ASSIGNED,
                    recipient=new_schedule.technician,
                    related_object=new_schedule,
                    message=(
                        f"New routine maintenance schedule created for elevator {new_schedule.elevator.machine_number}. "
                        f"Scheduled for: {next_date.strftime('%Y-%m-%d %H:%M')}"
                    )
                )

            return new_schedule

        except IntegrityError:
            # Handle race condition - return the schedule that was created by another process
            return MaintenanceSchedule.objects.get(
                elevator=maintenance_schedule.elevator,
                scheduled_date=next_date
            )

    def _check_and_handle_overdue_status(self, maintenance_schedule):
        """
        Check if a schedule is overdue and send alerts if it just became overdue.
        """
        if (maintenance_schedule.scheduled_date < timezone.now() and 
            maintenance_schedule.status == 'scheduled'):
            
            maintenance_schedule.status = 'overdue'
            maintenance_schedule.save()

            # Generate next schedule if this is a routine maintenance
            next_schedule = self._generate_next_schedule(maintenance_schedule)

            # Common message for all recipients
            elevator = maintenance_schedule.elevator
            base_message = (
                f"Maintenance schedule for elevator {elevator.machine_number} "
                f"in building {elevator.building.name} is now overdue. "
                f"Original scheduled date: {maintenance_schedule.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
            )

            if next_schedule:
                base_message += f"\nNext maintenance scheduled for: {next_schedule.scheduled_date.strftime('%Y-%m-%d %H:%M')}"

            # Send alerts to all relevant parties
            if maintenance_schedule.technician:
                AlertService.create_alert(
                    alert_type=AlertType.TASK_OVERDUE,
                    recipient=maintenance_schedule.technician,
                    related_object=maintenance_schedule,
                    message=f"{base_message}\nPlease complete the maintenance as soon as possible."
                )

            if maintenance_schedule.maintenance_company:
                AlertService.create_alert(
                    alert_type=AlertType.TASK_OVERDUE,
                    recipient=maintenance_schedule.maintenance_company,
                    related_object=maintenance_schedule,
                    message=f"{base_message}\nPlease ensure this maintenance is completed promptly."
                )

            if elevator.building.developer:
                AlertService.create_alert(
                    alert_type=AlertType.TASK_OVERDUE,
                    recipient=elevator.building.developer,
                    related_object=maintenance_schedule,
                    message=f"{base_message}\nThe maintenance company has been notified."
                )

    def _handle_already_completed(self, maintenance_schedule):
        """Handle attempt to complete an already completed schedule."""
        return Response(
            {"detail": "Sorry, this maintenance schedule has already been completed!"},
            status=status.HTTP_400_BAD_REQUEST
        )

    def _handle_overdue_status(self, maintenance_schedule):
        """Handle completion of an overdue schedule."""
        maintenance_schedule.status = 'completed'
        maintenance_schedule.save()
        
        next_schedule = self._generate_next_schedule(maintenance_schedule)
        
        serializer = MaintenanceScheduleSerializer(maintenance_schedule)
        response_data = {
            "detail": "The maintenance schedule was overdue and has now been marked as completed.",
            "schedule": serializer.data
        }
        
        if next_schedule:
            next_serializer = MaintenanceScheduleSerializer(next_schedule)
            response_data["next_schedule"] = next_serializer.data
            response_data["detail"] += f" Next maintenance scheduled for {next_schedule.scheduled_date.strftime('%Y-%m-%d %H:%M')}."
        
        return Response(response_data, status=status.HTTP_200_OK)

    def _handle_scheduled_status(self, maintenance_schedule):
        """Handle completion of a scheduled maintenance."""
        maintenance_schedule.status = 'completed'
        maintenance_schedule.save()
        
        next_schedule = self._generate_next_schedule(maintenance_schedule)
        
        serializer = MaintenanceScheduleSerializer(maintenance_schedule)
        response_data = {
            "detail": "The maintenance schedule has been completed.",
            "schedule": serializer.data
        }
        
        if next_schedule:
            next_serializer = MaintenanceScheduleSerializer(next_schedule)
            response_data["next_schedule"] = next_serializer.data
            response_data["detail"] += f" Next maintenance scheduled for {next_schedule.scheduled_date.strftime('%Y-%m-%d %H:%M')}."
        
        return Response(response_data, status=status.HTTP_200_OK)

class CreateBuildingAdhocScheduleView(APIView):
    """
    API endpoint to create a new building-specific ad hoc maintenance schedule.
    Uses UUIDs for all resource identifiers.
    """
    permission_classes = [AllowAny]

    def validate_uuid(self, uuid_str):
        """Validate and return UUID from string or return it if already a UUID"""
        if isinstance(uuid_str, UUID):
            return uuid_str  # Already a UUID, return as is
        try:
            return UUID(str(uuid_str))  # Convert to UUID if it's a string
        except ValueError:
            raise serializers.ValidationError("Invalid UUID format")

    def get_related_elevator(self, building):
        """Retrieve first elevator for building with related objects"""
        return Elevator.objects.select_related(
            'technician',
            'maintenance_company'
        ).filter(building=building).first()

    @swagger_auto_schema(
        request_body=AdhocScheduleCreateSerializer,
        manual_parameters=[
            openapi.Parameter(
                'building_id', openapi.IN_PATH,
                description="UUID of the building",
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True
            )
        ],
        responses={
            201: BuildingLevelAdhocScheduleSerializer,
            400: openapi.Response("Invalid input data"),
            404: openapi.Response("Building or related resource not found")
        }
    )
    def post(self, request, building_id):
        """Create an ad hoc maintenance schedule for a given building"""

        # Validate building UUID format
        try:
            building_uuid = self.validate_uuid(building_id)
        except serializers.ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve building instance
        try:
            building = Building.objects.get(id=building_uuid)
        except Building.DoesNotExist:
            return Response(
                {'detail': f'Building {building_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate input data
        input_serializer = AdhocScheduleCreateSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve elevator with related objects
        elevator = self.get_related_elevator(building)
        if not elevator:
            return Response(
                {'detail': f'No elevators found for building {building_id}'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate required relations
        required_relations = {
            'technician': elevator.technician,
            'maintenance_company': elevator.maintenance_company
        }

        for field, value in required_relations.items():
            if not value:
                return Response(
                    {'detail': f'Missing {field.replace("_", " ")} for elevator {elevator.id}'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Create ad hoc schedule
        try:
            adhoc_schedule = BuildingLevelAdhocSchedule.objects.create(
                building=building,
                technician=elevator.technician,
                maintenance_company=elevator.maintenance_company,
                description=input_serializer.validated_data['description'],
                scheduled_date=now(),
                status='scheduled'
            )
        except ValidationError as e:
            return Response(
                {'detail': f'Validation error: {dict(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Return created schedule
        output_serializer = BuildingLevelAdhocScheduleSerializer(adhoc_schedule)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class CompleteBuildingScheduleView(APIView):
    """
    API View to handle completion of building-level maintenance schedules.
    
    This view processes the completion of maintenance schedules for multiple elevators
    within a building by creating the necessary maintenance records, condition reports,
    and logs for each elevator. The technician needs to supply only the elevator UUIDs.
    
    Endpoint: POST /api/jobs/buildings/<uuid:building_schedule_id>/complete-schedule/
    
    Request body format:
    {
        "elevators": [
            "2c26e342-db96-4490-845c-f1b871004b34",
            "e8a7d210-3c1e-4c9c-a27b-0d44f0e4b5d2"
        ]
    }
    """
    permission_classes = [AllowAny]

    def _validate_building_schedule(self, building_schedule_id):
        try:
            building_schedule_uuid = UUID(str(building_schedule_id))
        except ValueError:
            return Response({
                "message": "Invalid building schedule ID format. Please provide a valid UUID."
            }, status=status.HTTP_400_BAD_REQUEST)

        building_schedule = get_object_or_404(BuildingLevelAdhocSchedule, id=building_schedule_uuid)

        if building_schedule.status == 'completed':
            return Response({
                "message": "This building schedule has already been completed."
            }, status=status.HTTP_400_BAD_REQUEST)

        return building_schedule

    def _validate_elevators(self, elevator_uuid_list, building):
        """
        Validate that each provided elevator UUID is valid and corresponds to an existing Elevator in the building.
        Returns a tuple: (list_of_failed_elevator_messages, validation_success_boolean)
        """
        failed_elevators = []

        for elevator_uuid in elevator_uuid_list:
            try:
                # Validate the UUID format
                UUID(str(elevator_uuid))
            except ValueError:
                failed_elevators.append(f"Elevator ID '{elevator_uuid}' is not a valid UUID.")
                continue

            elevator = Elevator.objects.filter(id=elevator_uuid, building=building).first()
            if not elevator:
                failed_elevators.append(f"Elevator with UUID '{elevator_uuid}' does not exist or does not belong to this building.")

        return failed_elevators, len(failed_elevators) == 0

    def _process_elevator(self, elevator_uuid, building, building_schedule):
        """
        Process a single elevator's maintenance records using default values.
        After the maintenance log is created, an alert is sent to the developer for approval.
        """
        try:
            elevator = get_object_or_404(Elevator, id=elevator_uuid, building=building)

            # Create the Ad-Hoc Maintenance Schedule
            ad_hoc_schedule = AdHocMaintenanceSchedule.objects.create(
                elevator=elevator,
                technician=building_schedule.technician,
                maintenance_company=building_schedule.maintenance_company,
                scheduled_date=building_schedule.scheduled_date,
                description=(
                    f"A system-generated maintenance schedule based on the building-level ad-hoc schedule of "
                    f"{building_schedule.scheduled_date.strftime('%Y-%m-%d')}, intended to {building_schedule.description}."
                ),
                status='completed'
            )

            # Create a default Condition Report
            condition_report = AdHocElevatorConditionReport.objects.create(
                ad_hoc_schedule=ad_hoc_schedule,
                technician=building_schedule.technician,
                date_inspected=timezone.now(),
                components_checked="Default components check - all components normal.",
                condition="Good"
            )

            # Create a default Maintenance Log
            maintenance_log = AdHocMaintenanceLog.objects.create(
                ad_hoc_schedule=ad_hoc_schedule,
                technician=building_schedule.technician,
                condition_report=condition_report,
                date_completed=timezone.now(),
                summary_title="Auto-generated maintenance log",
                description="Maintenance log auto-generated based on building-level schedule completion.",
                overseen_by="System"
            )

            # Send Alert to Developer for review
            # Assumes the building (or building_schedule.building) has a 'developer' attribute.
            if hasattr(building, 'developer') and building.developer:
                AlertService.create_alert(
                    alert_type=AlertType.LOG_ADDED,
                    recipient=building.developer,
                    related_object=ad_hoc_schedule,
                    message=(
                        f"New maintenance log added for elevator {elevator.machine_number} by technician {building_schedule.technician}. "
                        f"Please review and approve."
                    )
                )
            else:
                logger.warning(
                    f"Developer not found for building {building.id}; no alert sent for elevator {elevator.machine_number}."
                )

            return elevator.user_name, None
        except Exception as e:
            logger.error(f"Error processing elevator with UUID {elevator_uuid}: {str(e)}")
            return None, f"Error processing elevator with UUID {elevator_uuid}: {str(e)}"

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'elevators': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, format="uuid"),
                    description="List of elevator UUIDs"
                )
            },
            example={
                "elevators": [
                    "2c26e342-db96-4490-845c-f1b871004b34",
                    "e8a7d210-3c1e-4c9c-a27b-0d44f0e4b5d2"
                ]
            }
        ),
        operation_description="Complete a building-level maintenance schedule using only elevator UUIDs",
        responses={
            200: openapi.Response(
                description="Schedule completion status",
                examples={
                    "application/json": {
                        "message": "Success message",
                        "failed_elevators": ["List of errors if any"]
                    }
                }
            ),
            400: openapi.Response(
                description="Bad request",
                examples={
                    "application/json": {
                        "message": "Error message",
                        "failed_elevators": ["Details about invalid data"]
                    }
                }
            ),
            404: openapi.Response(
                description="Not found",
                examples={
                    "application/json": {
                        "message": "Building schedule not found"
                    }
                }
            )
        },
        manual_parameters=[
            openapi.Parameter(
                name='building_schedule_id',
                in_=openapi.IN_PATH,
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_UUID,
                required=True,
                description="UUID of the building schedule"
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        """Handle POST request to complete building schedule."""
        # Validate and get building schedule
        building_schedule = self._validate_building_schedule(kwargs['building_schedule_id'])
        if isinstance(building_schedule, Response):
            return building_schedule

        building = building_schedule.building
        elevator_uuid_list = request.data.get("elevators", [])

        # Validate all provided elevator UUIDs
        failed_elevators, is_valid = self._validate_elevators(elevator_uuid_list, building)
        if not is_valid:
            return Response({
                "message": "Some elevators do not belong to this building or do not exist.",
                "failed_elevators": failed_elevators
            }, status=status.HTTP_400_BAD_REQUEST)

        # Process each elevator
        successful_elevators = []
        for elevator_uuid in elevator_uuid_list:
            elevator_name, error = self._process_elevator(elevator_uuid, building, building_schedule)
            if elevator_name:
                successful_elevators.append(elevator_name)
            if error:
                failed_elevators.append(error)

        # Update building schedule status to 'completed' if all processing was successful
        if not failed_elevators:
            building_schedule.status = 'completed'
            building_schedule.save()

        # Prepare the response message
        if successful_elevators:
            message = (
                f"{len(successful_elevators)} elevator(s) ({', '.join(successful_elevators)}) were successfully processed. "
                "Their condition reports and maintenance logs were generated and recorded."
            )
        else:
            message = "No elevators were successfully processed."

        if failed_elevators:
            message = "Some errors occurred: " + "; ".join(failed_elevators)

        return Response({
            "message": message,
            "failed_elevators": failed_elevators
        }, status=status.HTTP_200_OK)


class MaintenanceScheduleDeleteView(APIView):
    """
    View to delete a maintenance schedule, handling regular, ad-hoc, and building-level ad-hoc schedules.
    Uses UUIDs for consistent identification.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def delete(self, request, schedule_id):
        # Ensure the schedule_id is a string before converting to UUID
        try:
            schedule_uuid = UUID(str(schedule_id))  # Convert to string before creating UUID
        except ValueError:
            return Response({"detail": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)

        # Define a list of models to check for the schedule
        models_to_check = [
            (MaintenanceSchedule, "Regular maintenance schedule"),
            (AdHocMaintenanceSchedule, "Ad-hoc maintenance schedule"),
            (BuildingLevelAdhocSchedule, "Building-level ad-hoc maintenance schedule"),
        ]

        # Iterate through the models and attempt to delete the schedule
        for model, description in models_to_check:
            try:
                schedule = model.objects.get(id=schedule_uuid)
                schedule.delete()
                return Response({"detail": f"{description} deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                continue  # Move to the next model if the schedule is not found

        # If no schedule is found in any model, return a 404 response
        return Response({"detail": "Schedule not found."}, status=status.HTTP_404_NOT_FOUND)

class ElevatorMaintenanceSchedulesView(APIView):
    """
    View to retrieve all maintenance schedules (regular, ad-hoc, and building-level ad-hoc) associated with a specific elevator.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get(self, request, elevator_id):
        """
        Retrieve all maintenance schedules for a specific elevator.
        
        Args:
            request: The HTTP request object.
            elevator_id (UUID): The UUID of the elevator to retrieve schedules for.
        
        Returns:
            Response: A JSON response containing the maintenance schedules or an error message.
        """
        # Fetch the Elevator object using the provided elevator_id
        elevator = get_object_or_404(Elevator, id=elevator_id)
        
        # Get all maintenance schedules for the elevator and evaluate the querysets immediately
        regular_schedules = list(MaintenanceSchedule.objects.filter(elevator=elevator))
        adhoc_schedules = list(AdHocMaintenanceSchedule.objects.filter(elevator=elevator))
        building_adhoc_schedules = list(BuildingLevelAdhocSchedule.objects.filter(building=elevator.building))
        
        # Check if no schedules are found using the evaluated lists
        if not any([regular_schedules, adhoc_schedules, building_adhoc_schedules]):
            return Response(
                {"detail": "No maintenance schedules found for this elevator."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Serialize the maintenance schedules
        regular_serializer = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
        adhoc_serializer = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
        building_adhoc_serializer = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)
        
        # Combine serialized data
        response_data = {
            "regular_schedules": regular_serializer.data,
            "adhoc_schedules": adhoc_serializer.data,
            "building_adhoc_schedules": building_adhoc_serializer.data,
        }
        
        return Response(response_data, status=status.HTTP_200_OK)

class TechnicianMaintenanceSchedulesView(APIView):
    """
    View to retrieve all maintenance schedules (regular, ad-hoc, and building-level ad-hoc) assigned to a technician.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get_technician(self, technician_id):
        """
        Fetch the TechnicianProfile object using the provided technician_id (UUID).
        """
        try:
            # Convert technician_id to string if it's a UUID object
            technician_id_str = str(technician_id)
            # Validate if the technician_id is a valid UUID
            UUID(technician_id_str, version=4)
            technician = TechnicianProfile.objects.get(id=technician_id)
            return technician
        except (ValueError, ValidationError):
            return None
        except TechnicianProfile.DoesNotExist:
            return None

    def update_schedule_status(self, schedule):
        """
        Update the status of a schedule to 'overdue' if needed.
        """
        current_time = timezone.now()
        if schedule.scheduled_date < current_time and schedule.status == 'scheduled':
            schedule.status = 'overdue'
            schedule.save()
        return schedule

    def get_schedules(self, technician):
        """
        Fetch all maintenance schedules for the given technician and update their status if needed.
        """
        # Get all schedules
        regular_schedules = MaintenanceSchedule.objects.filter(technician=technician)
        adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(technician=technician)
        building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.filter(technician=technician)

        # Update status for overdue schedules
        for schedule in regular_schedules:
            self.update_schedule_status(schedule)
        for schedule in adhoc_schedules:
            self.update_schedule_status(schedule)
        for schedule in building_adhoc_schedules:
            self.update_schedule_status(schedule)

        return regular_schedules, adhoc_schedules, building_adhoc_schedules

    def serialize_schedules(self, regular_schedules, adhoc_schedules, building_adhoc_schedules):
        """
        Serialize the maintenance schedules.
        """
        regular_serializer = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
        adhoc_serializer = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
        building_adhoc_serializer = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)
        return regular_serializer, adhoc_serializer, building_adhoc_serializer

    def get(self, request, technician_id):
        """
        Handle GET request to retrieve maintenance schedules for a technician.
        """
        technician = self.get_technician(technician_id)
        if not technician:
            return Response({"detail": "Technician not found."}, status=status.HTTP_404_NOT_FOUND)

        regular_schedules, adhoc_schedules, building_adhoc_schedules = self.get_schedules(technician)
        
        if not (regular_schedules.exists() or adhoc_schedules.exists() or building_adhoc_schedules.exists()):
            return Response(
                {"detail": "No maintenance schedules found for this technician."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        regular_serializer, adhoc_serializer, building_adhoc_serializer = self.serialize_schedules(
            regular_schedules, adhoc_schedules, building_adhoc_schedules
        )

        response_data = {
            "regular_schedules": regular_serializer.data,
            "adhoc_schedules": adhoc_serializer.data,
            "building_adhoc_schedules": building_adhoc_serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

class MaintenanceScheduleListView(APIView):
    """
    View to retrieve all maintenance schedules, including regular, ad-hoc, and building-level ad-hoc schedules.
    This view is scalable and uses UUIDs for consistency with the project.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get(self, request):
        try:
            # Extract query parameters for filtering (if needed)
            elevator_id = request.query_params.get('elevator_id')
            building_id = request.query_params.get('building_id')
            technician_id = request.query_params.get('technician_id')

            # Initialize querysets
            regular_schedules = MaintenanceSchedule.objects.all()
            adhoc_schedules = AdHocMaintenanceSchedule.objects.all()
            building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.all()

            # Apply filters if UUIDs are provided
            if elevator_id:
                try:
                    elevator_uuid = UUID(elevator_id)
                    regular_schedules = regular_schedules.filter(elevator_id=elevator_uuid)
                    adhoc_schedules = adhoc_schedules.filter(elevator_id=elevator_uuid)
                except ValueError:
                    return Response(
                        {"detail": "Invalid elevator_id format. Must be a valid UUID."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if building_id:
                try:
                    building_uuid = UUID(building_id)
                    building_adhoc_schedules = building_adhoc_schedules.filter(building_id=building_uuid)
                except ValueError:
                    return Response(
                        {"detail": "Invalid building_id format. Must be a valid UUID."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            if technician_id:
                try:
                    technician_uuid = UUID(technician_id)
                    regular_schedules = regular_schedules.filter(technician_id=technician_uuid)
                    adhoc_schedules = adhoc_schedules.filter(technician_id=technician_uuid)
                except ValueError:
                    return Response(
                        {"detail": "Invalid technician_id format. Must be a valid UUID."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Serialize data
            regular_serializer = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
            adhoc_serializer = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
            building_adhoc_serializer = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)

            # Combine the serialized data
            response_data = {
                "regular_schedules": regular_serializer.data,
                "adhoc_schedules": adhoc_serializer.data,
                "building_level_adhoc_schedules": building_adhoc_serializer.data,
            }

            # Return the combined data
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            # Handle unexpected errors gracefully
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class MaintenanceCompanyMaintenanceSchedulesView(APIView):
    """
    View to retrieve all maintenance schedules (regular, ad-hoc, and building-level ad-hoc) associated with a specific maintenance company.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get(self, request, company_id):
        try:
            # Ensure company_id is treated as a string and converted to UUID
            company_uuid = UUID(str(company_id))
            
            # Fetch the MaintenanceCompanyProfile object using the provided company_uuid
            maintenance_company = MaintenanceCompanyProfile.objects.get(id=company_uuid)
        except MaintenanceCompanyProfile.DoesNotExist:
            return JsonResponse({"detail": "Maintenance company not found."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return JsonResponse({"detail": "Invalid UUID format."}, status=status.HTTP_400_BAD_REQUEST)

        # Get all regular maintenance schedules for the company
        regular_schedules = MaintenanceSchedule.objects.filter(maintenance_company=maintenance_company)
        # Get all ad-hoc maintenance schedules for the company
        adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(maintenance_company=maintenance_company)
        # Get all building-level ad-hoc maintenance schedules for the company
        building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.filter(maintenance_company=maintenance_company)
        
        # Check if no schedules are found
        if not (regular_schedules.exists() or adhoc_schedules.exists() or building_adhoc_schedules.exists()):
            return JsonResponse({"detail": "No maintenance schedules found for this maintenance company."}, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize the maintenance schedules
        regular_serializer = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
        adhoc_serializer = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
        building_adhoc_serializer = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)
        
        # Combine serialized data
        response_data = {
            "regular_schedules": regular_serializer.data,
            "adhoc_schedules": adhoc_serializer.data,
            "building_adhoc_schedules": building_adhoc_serializer.data,
        }
        
        return JsonResponse(response_data, status=status.HTTP_200_OK)

class DeveloperMaintenanceSchedulesView(APIView):
    """
    View to retrieve all maintenance schedules (regular, ad-hoc, and building-level ad-hoc) associated with a developer.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get(self, request, developer_id):
        try:
            # Use DeveloperProfile model here, as that's the correct model name
            developer = DeveloperProfile.objects.get(id=developer_id)
        except DeveloperProfile.DoesNotExist:
            return Response({"detail": "Developer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get all buildings linked to this developer
        buildings = developer.buildings.all()
        if not buildings.exists():
            return Response({"detail": "No buildings found for this developer."}, status=status.HTTP_404_NOT_FOUND)

        # Get all elevators linked to these buildings
        elevators = Elevator.objects.filter(building__in=buildings)
        if not elevators.exists():
            return Response({"detail": "No elevators found for this developer."}, status=status.HTTP_404_NOT_FOUND)

        # Get all regular, ad-hoc, and building-level ad-hoc maintenance schedules for these elevators and buildings
        regular_schedules = MaintenanceSchedule.objects.filter(elevator__in=elevators)
        adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(elevator__in=elevators)
        building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.filter(building__in=buildings)

        # Check if no maintenance schedules are found
        if not (regular_schedules.exists() or adhoc_schedules.exists() or building_adhoc_schedules.exists()):
            return Response({"detail": "No maintenance schedules found for this developer."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the schedules
        regular_serializer = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
        adhoc_serializer = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
        building_adhoc_serializer = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)

        # Combine serialized data
        response_data = {
            "regular_schedules": regular_serializer.data,
            "adhoc_schedules": adhoc_serializer.data,
            "building_adhoc_schedules": building_adhoc_serializer.data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

class BuildingMaintenanceSchedulesView(APIView):
    """
    View to retrieve all maintenance schedules (regular, ad-hoc, and building-level ad-hoc) for a specific building.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    def get_building(self, building_id: UUID):
        """
        Fetch the Building object using the provided building_id (UUID).
        """
        try:
            return Building.objects.get(id=building_id)
        except Building.DoesNotExist:
            return None

    def get_elevators_for_building(self, building: Building):
        """
        Fetch all elevators linked to the given building.
        """
        return building.elevators.all()

    def get_maintenance_schedules(self, elevators):
        """
        Fetch all regular and ad-hoc maintenance schedules for the given elevators.
        """
        regular_schedules = MaintenanceSchedule.objects.filter(elevator__in=elevators)
        adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(elevator__in=elevators)
        return regular_schedules, adhoc_schedules

    def get_building_level_adhoc_schedules(self, building: Building):
        """
        Fetch all building-level ad-hoc maintenance schedules for the given building.
        """
        return BuildingLevelAdhocSchedule.objects.filter(building=building)

    def serialize_schedules(self, regular_schedules, adhoc_schedules, building_adhoc_schedules):
        """
        Serialize the maintenance schedules.
        """
        regular_serializer = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
        adhoc_serializer = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
        building_adhoc_serializer = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)
        return regular_serializer.data, adhoc_serializer.data, building_adhoc_serializer.data

    def get(self, request, building_id: UUID):
        """
        Handle GET request to retrieve maintenance schedules for a specific building.
        """
        # Validate building_id format
        try:
            UUID(str(building_id))  # Ensure the building_id is a valid UUID
        except ValueError:
            return Response({"detail": "Invalid building ID format."}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the building
        building = self.get_building(building_id)
        if not building:
            return Response({"detail": "Building not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch elevators for the building
        elevators = self.get_elevators_for_building(building)
        if not elevators.exists():
            return Response({"detail": "No elevators found for this building."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch maintenance schedules
        regular_schedules, adhoc_schedules = self.get_maintenance_schedules(elevators)
        building_adhoc_schedules = self.get_building_level_adhoc_schedules(building)

        # Check if no maintenance schedules are found
        if (
            not regular_schedules.exists()
            and not adhoc_schedules.exists()
            and not building_adhoc_schedules.exists()
        ):
            return Response({"detail": "No maintenance schedules found for this building."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the schedules
        regular_data, adhoc_data, building_adhoc_data = self.serialize_schedules(
            regular_schedules, adhoc_schedules, building_adhoc_schedules
        )

        # Combine serialized data into a structured response
        response_data = {
            "regular_schedules": regular_data,
            "adhoc_schedules": adhoc_data,
            "building_level_adhoc_schedules": building_adhoc_data,
        }

        return Response(response_data, status=status.HTTP_200_OK)

class ChangeTechnicianView(APIView):
    permission_classes = [AllowAny]

    # Define request body schema
    request_body_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['technician_id'],
        properties={
            'technician_id': openapi.Schema(
                type=openapi.TYPE_STRING, 
                description='UUID of the new technician to be assigned'
            ),
        }
    )

    # Define response schemas
    responses = {
        status.HTTP_200_OK: openapi.Response(
            description="Success",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Success message with new technician name'
                    )
                }
            )
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Bad Request",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Error message'
                    )
                }
            )
        ),
        status.HTTP_404_NOT_FOUND: openapi.Response(
            description="Not Found",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'detail': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Error message'
                    )
                }
            )
        )
    }

    @swagger_auto_schema(
        operation_description="Change the technician assigned to a maintenance schedule",
        operation_summary="Change assigned technician",
        manual_parameters=[
            openapi.Parameter(
                'schedule_type',
                openapi.IN_PATH,
                description="Type of schedule (regular, adhoc, or building)",
                type=openapi.TYPE_STRING,
                enum=['regular', 'adhoc', 'building']
            ),
            openapi.Parameter(
                'schedule_id',
                openapi.IN_PATH,
                description="UUID of the maintenance schedule",
                type=openapi.TYPE_STRING,
                format='uuid'
            )
        ],
        request_body=request_body_schema,
        responses=responses
    )
    def put(self, request, schedule_type: str, schedule_id: UUID):
        """
        Change the technician assigned to a maintenance schedule (regular, ad-hoc, or building-level ad-hoc).
        Ensures proper validation of technician and schedule type-specific handling.
        """
        # Validate technician_id UUID FIRST
        technician_id = request.data.get('technician_id', None)
        if not technician_id:
            return Response(
                {"detail": "Technician ID must be provided."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            technician_id = UUID(technician_id)
        except ValueError:
            return Response(
                {"detail": "Invalid Technician ID format. Must be a valid UUID."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate schedule type
        if schedule_type not in ['regular', 'adhoc', 'building']:
            return Response(
                {"detail": "Invalid schedule type. Use 'regular', 'adhoc', or 'building'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the appropriate schedule based on type
        schedule = None
        if schedule_type == 'regular':
            schedule = MaintenanceSchedule.objects.filter(id=schedule_id).first()
        elif schedule_type == 'adhoc':
            schedule = AdHocMaintenanceSchedule.objects.filter(id=schedule_id).first()
        elif schedule_type == 'building':
            schedule = BuildingLevelAdhocSchedule.objects.filter(id=schedule_id).first()

        if not schedule:
            return Response(
                {"detail": "Maintenance schedule not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if the maintenance schedule status is 'completed'
        if schedule.status == 'completed':
            return Response(
                {"detail": "You cannot reassign a completed schedule."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch the TechnicianProfile object
        try:
            technician = TechnicianProfile.objects.get(id=technician_id)
        except TechnicianProfile.DoesNotExist:
            return Response(
                {"detail": f"Technician with ID {technician_id} does not exist."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if technician is from the same maintenance company as the schedule
        if technician.maintenance_company != schedule.maintenance_company:
            return Response(
                {"detail": "Technician is not linked to the same maintenance company as this maintenance schedule."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the technician for any schedule type by updating the instance and saving
        schedule.technician = technician
        schedule.save()

        # Return success response
        technician_user = technician.user
        return Response(
            {
                "message": f"Technician has been changed to {technician_user.first_name} {technician_user.last_name}."
            },
            status=status.HTTP_200_OK
        )

class MaintenanceScheduleNullTechnicianFilterView(APIView):
    permission_classes = [AllowAny]

    def put(self, request):
        """
        Fetch maintenance schedules where the technician field is null.
        Allows filtering by developer, building, maintenance company, scheduled date, or elevator.
        """
        allowed_fields = {'developer_id', 'building_id', 'scheduled_date', 'maintenance_company_id', 'elevator_id'}
        request_keys = set(request.data.keys())
        
        # Validate request fields
        if invalid_fields := request_keys - allowed_fields:
            return Response({"detail": f"Invalid fields: {', '.join(invalid_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        
        filters = {
            "developer_id": request.data.get("developer_id"),
            "building_id": request.data.get("building_id"),
            "scheduled_date": request.data.get("scheduled_date"),
            "maintenance_company_id": request.data.get("maintenance_company_id"),
            "elevator_id": request.data.get("elevator_id"),
        }

        queryset = MaintenanceSchedule.objects.filter(technician__isnull=True)

        # Filter by Developer
        if filters["developer_id"]:
            try:
                developer = DeveloperProfile.objects.get(id=filters["developer_id"])
                buildings = Building.objects.filter(developer=developer)
                elevators = Elevator.objects.filter(building__in=buildings)
                queryset = queryset.filter(elevator__in=elevators)
            except DeveloperProfile.DoesNotExist:
                return Response({"detail": f"Developer with ID {filters['developer_id']} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Filter by Building
        if filters["building_id"]:
            try:
                building = Building.objects.get(id=filters["building_id"])
                queryset = queryset.filter(elevator__building=building)
            except Building.DoesNotExist:
                return Response({"detail": f"Building with ID {filters['building_id']} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Filter by Scheduled Date
        if filters["scheduled_date"]:
            try:
                scheduled_date = datetime.strptime(filters["scheduled_date"], "%Y-%m-%d").date()
                queryset = queryset.filter(scheduled_date=scheduled_date)
            except ValueError:
                return Response({"detail": "Invalid date format. Please use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # Filter by Maintenance Company
        if filters["maintenance_company_id"]:
            try:
                maintenance_company = MaintenanceCompanyProfile.objects.get(id=filters["maintenance_company_id"])
                queryset = queryset.filter(maintenance_company=maintenance_company)
            except MaintenanceCompanyProfile.DoesNotExist:
                return Response({"detail": f"Maintenance company with ID {filters['maintenance_company_id']} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Filter by Elevator
        if filters["elevator_id"]:
            try:
                elevator = Elevator.objects.get(id=filters["elevator_id"])
                queryset = queryset.filter(elevator=elevator)
            except Elevator.DoesNotExist:
                return Response({"detail": f"Elevator with ID {filters['elevator_id']} not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if results exist
        if not queryset.exists():
            return Response({"detail": "No non-assigned maintenance schedules found matching the criteria."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize response
        serializer = FullMaintenanceScheduleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MaintenanceScheduleFilterView(APIView):
    """
    Filter maintenance schedules (regular, ad-hoc, and building-level ad-hoc) based on various criteria.
    Applies filters one-by-one and checks for matches across all schedule types.
    """
    permission_classes = [ ]  # Adjust permissions as needed

    @swagger_auto_schema(
        operation_description="Filter maintenance schedules based on various criteria",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'schedule_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["regular", "adhoc", "building"],
                    description="Type of schedule to filter"
                ),
                'technician_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uuid",
                    description="UUID of the technician"
                ),
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['scheduled', 'overdue', 'completed'],
                    description="Status of the maintenance schedule"
                ),
                'developer_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uuid",
                    description="UUID of the developer"
                ),
                'elevator_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uuid",
                    description="UUID of the elevator"
                ),
                'building_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uuid",
                    description="UUID of the building"
                ),
                'scheduled_date': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="date",
                    description="Date of scheduled maintenance (YYYY-MM-DD)"
                ),
                'next_schedule': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['1_month', '3_months', '6_months', 'set_date'],
                    description="Next schedule interval"
                ),
                'maintenance_company_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format="uuid",
                    description="UUID of the maintenance company"
                ),
            }
        ),
        responses={
            200: openapi.Response('Successful operation', CompleteMaintenanceScheduleSerializer),
            400: 'Bad Request - Invalid input parameters',
            404: 'Not Found - No matching schedules found'
        },
        operation_summary="Filter Maintenance Schedules"
    )
    def put(self, request):
        # Allowed fields
        allowed_fields = [
            'technician_id', 'status', 'developer_id', 'elevator_id',
            'building_id', 'scheduled_date', 'next_schedule', 'maintenance_company_id', 'schedule_type'
        ]

        # Check for any invalid keys in the request data
        invalid_fields = [key for key in request.data if key not in allowed_fields]
        if invalid_fields:
            return Response(
                {"detail": f"Invalid fields: {', '.join(invalid_fields)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Extract filters
        filters = {key: request.data.get(key) for key in allowed_fields}

        # Valid options for status and next_schedule
        valid_statuses = ['scheduled', 'overdue', 'completed']
        valid_next_schedules = ['1_month', '3_months', '6_months', 'set_date']

        # Determine schedule_type
        schedule_type = filters.get("schedule_type")
        if schedule_type not in [None, "regular", "adhoc", "building"]:
            return Response(
                {"detail": "Invalid schedule_type. Valid options are: 'regular', 'adhoc', 'building'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Initialize queryset based on schedule_type
        if schedule_type == "regular":
            queryset = MaintenanceSchedule.objects.all()
        elif schedule_type == "adhoc":
            queryset = AdHocMaintenanceSchedule.objects.all()
        elif schedule_type == "building":
            queryset = BuildingLevelAdhocSchedule.objects.all()
        else:
            # Combined queryset across all types
            queryset = list(MaintenanceSchedule.objects.all()) + \
                       list(AdHocMaintenanceSchedule.objects.all()) + \
                       list(BuildingLevelAdhocSchedule.objects.all())

        # Apply each filter one-by-one
        for key, value in filters.items():
            if not value or key == "schedule_type":
                continue

            if key == "technician_id":
                try:
                    technician_uuid = uuid.UUID(value)
                except ValueError:
                    return Response({"detail": "Invalid technician ID format."}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    technician = TechnicianProfile.objects.get(id=technician_uuid)
                except TechnicianProfile.DoesNotExist:
                    return Response({"detail": f"Technician with ID {value} not found."}, status=status.HTTP_404_NOT_FOUND)
                queryset = [item for item in queryset if item.technician == technician]

            elif key == "status":
                if value not in valid_statuses:
                    return Response({"detail": f"Invalid status '{value}'. Valid options are: {', '.join(valid_statuses)}."}, status=status.HTTP_400_BAD_REQUEST)
                queryset = [item for item in queryset if item.status == value]

            elif key == "developer_id":
                try:
                    developer_uuid = uuid.UUID(value)
                except ValueError:
                    return Response({"detail": "Invalid developer ID format."}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    developer = DeveloperProfile.objects.get(id=developer_uuid)
                except DeveloperProfile.DoesNotExist:
                    return Response({"detail": f"Developer with ID {value} not found."}, status=status.HTTP_404_NOT_FOUND)
                buildings = Building.objects.filter(developer=developer)
                elevators = Elevator.objects.filter(building__in=buildings)
                # Only filter items that have an 'elevator' attribute
                queryset = [item for item in queryset if hasattr(item, 'elevator') and item.elevator in elevators]

            elif key == "elevator_id":
                try:
                    elevator_uuid = uuid.UUID(value)
                except ValueError:
                    return Response({"detail": "Invalid elevator ID format."}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    elevator = Elevator.objects.get(id=elevator_uuid)
                except Elevator.DoesNotExist:
                    return Response({"detail": f"Elevator with ID {value} not found."}, status=status.HTTP_404_NOT_FOUND)
                queryset = [item for item in queryset if hasattr(item, 'elevator') and item.elevator == elevator]

            elif key == "building_id":
                try:
                    building_uuid = uuid.UUID(value)
                except ValueError:
                    return Response({"detail": "Invalid building ID format."}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    building = Building.objects.get(id=building_uuid)
                except Building.DoesNotExist:
                    return Response({"detail": f"Building with ID {value} not found."}, status=status.HTTP_404_NOT_FOUND)
                # For items with an elevator, check if elevator.building matches; for building-level schedules, check building field
                def in_building(item):
                    if hasattr(item, 'elevator') and item.elevator:
                        return item.elevator.building == building
                    elif hasattr(item, 'building'):
                        return item.building == building
                    return False
                queryset = [item for item in queryset if in_building(item)]

            elif key == "scheduled_date":
                try:
                    filter_date = datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    return Response({"detail": "Invalid date format. Please use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
                queryset = [item for item in queryset if item.scheduled_date.date() == filter_date]

            elif key == "next_schedule":
                if value not in valid_next_schedules:
                    return Response({"detail": f"Invalid next_schedule '{value}'. Valid options are: {', '.join(valid_next_schedules)}."}, status=status.HTTP_400_BAD_REQUEST)
                queryset = [item for item in queryset if item.next_schedule == value]

            elif key == "maintenance_company_id":
                try:
                    company_uuid = uuid.UUID(value)
                except ValueError:
                    return Response({"detail": "Invalid maintenance company ID format."}, status=status.HTTP_400_BAD_REQUEST)
                try:
                    maintenance_company = MaintenanceCompanyProfile.objects.get(id=company_uuid)
                except MaintenanceCompanyProfile.DoesNotExist:
                    return Response({"detail": f"Maintenance company with ID {value} not found."}, status=status.HTTP_404_NOT_FOUND)
                queryset = [item for item in queryset if item.maintenance_company == maintenance_company]

        if not queryset:
            return Response({"detail": "No maintenance schedules found matching the criteria."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the queryset using the proper serializer based on schedule_type
        if schedule_type == "building":
            serializer = BuildingLevelAdhocScheduleSerializer(queryset, many=True)
        else:
            serializer = CompleteMaintenanceScheduleSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class MaintenanceCompanyJobStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, company_uuid, job_status):
        try:
            maintenance_company = MaintenanceCompanyProfile.objects.get(id=company_uuid)
        except MaintenanceCompanyProfile.DoesNotExist:
            return Response(
                {"detail": f"Maintenance company with UUID {company_uuid} not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        filter_mapping = {
            "upcoming_jobs": {
                "status": "scheduled",
                "date_filter": {"scheduled_date__gt": timezone.now()},
                "order_by": "scheduled_date"
            },
            "overdue_jobs": {
                "status": "overdue",
                "order_by": "-scheduled_date"
            },
            "completed_jobs": {
                "status": "completed",
                "order_by": "-scheduled_date"
            },
        }

        if job_status not in filter_mapping:
            return Response({
                "detail": "Invalid job_status provided. Valid options are 'upcoming_jobs', 'overdue_jobs', and 'completed_jobs'."
            }, status=status.HTTP_400_BAD_REQUEST)

        filter_options = filter_mapping[job_status]
        filter_kwargs = {
            "maintenance_company": maintenance_company,
            "status": filter_options["status"]
        }
        
        if "date_filter" in filter_options:
            filter_kwargs.update(filter_options["date_filter"])

        # Debugging output
        print(f"Filtering MaintenanceSchedule with: {filter_kwargs}")

        # Query and order schedules
        regular_schedules = MaintenanceSchedule.objects.filter(**filter_kwargs).order_by(filter_options["order_by"])
        adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(**filter_kwargs).order_by(filter_options["order_by"])
        building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.filter(**filter_kwargs).order_by(filter_options["order_by"])

        # Debugging output
        print(f"Found {regular_schedules.count()} regular schedules")
        print(f"Found {adhoc_schedules.count()} adhoc schedules")
        print(f"Found {building_adhoc_schedules.count()} building-level adhoc schedules")

        serialized_regular = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
        serialized_adhoc = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
        serialized_building_adhoc = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)

        return Response({
            'regular_schedules': serialized_regular.data,
            'adhoc_schedules': serialized_adhoc.data,
            'building_adhoc_schedules': serialized_building_adhoc.data,
        }, status=status.HTTP_200_OK)

class TechnicianJobStatusView(APIView):
    permission_classes = [AllowAny]

    """
    Retrieve regular, ad-hoc, and building-level ad-hoc maintenance schedules
    for a specific technician based on job status.
    """
    def get(self, request, technician_uuid, job_status):
        # Validate the technician UUID
        technician = get_object_or_404(TechnicianProfile, id=technician_uuid)

        # Filter MaintenanceSchedule, AdHocMaintenanceSchedule, and BuildingLevelAdhocSchedule for the technician
        regular_schedules = MaintenanceSchedule.objects.filter(technician=technician)
        adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(technician=technician)
        building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.filter(technician=technician)

        # Filter schedules based on job status
        if job_status == "upcoming_jobs":
            # Filter for scheduled jobs (upcoming jobs)
            regular_schedules = regular_schedules.filter(status="scheduled", scheduled_date__gte=timezone.now()).order_by('scheduled_date')
            adhoc_schedules = adhoc_schedules.filter(status="scheduled", scheduled_date__gte=timezone.now()).order_by('scheduled_date')
            building_adhoc_schedules = building_adhoc_schedules.filter(status="scheduled", scheduled_date__gte=timezone.now()).order_by('scheduled_date')

        elif job_status == "overdue_jobs":
            # Filter for overdue jobs
            regular_schedules = regular_schedules.filter(status="overdue", scheduled_date__lt=timezone.now()).order_by('-scheduled_date')
            adhoc_schedules = adhoc_schedules.filter(status="overdue", scheduled_date__lt=timezone.now()).order_by('-scheduled_date')
            building_adhoc_schedules = building_adhoc_schedules.filter(status="overdue", scheduled_date__lt=timezone.now()).order_by('-scheduled_date')

        elif job_status == "completed_jobs":
            # Filter for completed jobs
            regular_schedules = regular_schedules.filter(status="completed").order_by('-scheduled_date')
            adhoc_schedules = adhoc_schedules.filter(status="completed").order_by('-scheduled_date')
            building_adhoc_schedules = building_adhoc_schedules.filter(status="completed").order_by('-scheduled_date')

        else:
            return Response({
                "detail": "Invalid job_status provided. Valid options are 'upcoming_jobs', 'overdue_jobs', and 'completed_jobs'."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Serialize the data using the appropriate serializers
        serialized_regular_schedules = CompleteMaintenanceScheduleSerializer(regular_schedules, many=True)
        serialized_adhoc_schedules = CompleteMaintenanceScheduleSerializer(adhoc_schedules, many=True)
        serialized_building_adhoc_schedules = BuildingLevelAdhocScheduleSerializer(building_adhoc_schedules, many=True)

        # Return the serialized data
        return Response({
            'regular_schedules': serialized_regular_schedules.data,
            'adhoc_schedules': serialized_adhoc_schedules.data,
            'building_adhoc_schedules': serialized_building_adhoc_schedules.data,
        }, status=status.HTTP_200_OK)

class ElevatorMaintenanceHistoryView(APIView):
    permission_classes = [AllowAny]
    """
    Retrieve all completed maintenance schedules (regular and ad-hoc) for a specific elevator,
    including condition reports and maintenance logs, sorted by most recent.
    """

    def get(self, request, elevator_id: UUID):
        """
        Retrieves all completed maintenance schedules for a specific elevator.
        Includes both regular and ad-hoc schedules, sorted by the most recent.
        
        Args:
            request (Request): The HTTP request object.
            elevator_id (UUID): The UUID of the elevator.
        
        Returns:
            Response: A response containing the serialized maintenance schedules.
        """
        
        # Fetch completed maintenance schedules (regular and ad-hoc) for the elevator
        completed_regular_schedules = MaintenanceSchedule.objects.filter(
            elevator_id=elevator_id,
            status='completed'
        ).order_by('-scheduled_date')

        completed_adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(
            elevator_id=elevator_id,
            status='completed'
        ).order_by('-scheduled_date')

        # Combine and sort schedules by the most recent scheduled_date
        combined_schedules = list(completed_regular_schedules) + list(completed_adhoc_schedules)
        sorted_schedules = sorted(combined_schedules, key=lambda x: x.scheduled_date, reverse=True)

        # Serialize the sorted schedules
        serializer = CompleteMaintenanceScheduleSerializer(sorted_schedules, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class FileMaintenanceLogView(APIView):
    permission_classes = [AllowAny]

    maintenance_request_schema = openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['schedule_type', 'condition_report', 'maintenance_log'],
        properties={
            'schedule_type': openapi.Schema(
                type=openapi.TYPE_STRING,
                enum=['regular', 'adhoc'],
                description='Type of maintenance schedule'
            ),
            'condition_report': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['maintenance_schedule', 'technician'],
                properties={
                    'maintenance_schedule': openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        description='UUID of maintenance schedule'
                    ),
                    'technician': openapi.Schema(
                        type=openapi.TYPE_STRING, 
                        description='Technician ID'
                    ),
                    'alarm_bell': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        enum=['Functional', 'Intermittent', 'Non-Functional'],
                        description='Alarm bell condition'
                    ),
                    'noise_during_motion': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        enum=['Silent', 'Minimal', 'Moderate', 'Loud', 'Excessive'],
                        description='Noise during elevator operation'
                    ),
                    'cabin_lights': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        enum=['All Working', 'Partial Failure', 'Complete Failure'],
                        description='Cabin lighting system status'
                    ),
                    'additional_comments': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Additional technician observations'
                    )
                }
            ),
            'maintenance_log': openapi.Schema(
                type=openapi.TYPE_OBJECT,
                required=['performed_tasks'],
                properties={
                    'performed_tasks': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'task_name': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description='Name of maintenance task'
                                ),
                                'status': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    enum=['completed', 'partial', 'not_completed'],
                                    description='Task completion status'
                                ),
                                'observations': openapi.Schema(
                                    type=openapi.TYPE_STRING,
                                    description='Task-specific observations'
                                )
                            }
                        ),
                        description='List of performed maintenance tasks'
                    ),
                    'description': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Comprehensive maintenance description'
                    ),
                    'overseen_by': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Supervisor overseeing maintenance'
                    ),
                    'approved_by': openapi.Schema(
                        type=openapi.TYPE_STRING,
                        description='Maintenance approval authority'
                    ),
                    # Checklist fields
                    'check_machine_gear': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Checked machine gear"),
                    'check_machine_brake': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Checked machine brake"),
                    'check_controller_connections': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Checked controller connections"),
                    'blow_dust_from_controller': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Blown dust from controller"),
                    'clean_machine_room': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Cleaned machine room"),
                    'clean_guide_rails': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Cleaned guide rails"),
                    'observe_operation': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Observed operation"),
                }
            )
        }
    )

    @swagger_auto_schema(
        operation_description="File a comprehensive maintenance log with condition report",
        request_body=maintenance_request_schema,
        responses={
            200: openapi.Response(description="Maintenance log successfully created"),
            400: openapi.Response(description="Validation error"),
            404: openapi.Response(description="Schedule not found")
        }
    )
    def post(self, request, schedule_id):
        try:
            schedule_uuid = UUID(str(schedule_id).strip().lower())
        except (ValueError, AttributeError, TypeError):
            return Response(
                {"detail": "Invalid schedule ID format. Must be a valid UUID."},
                status=status.HTTP_400_BAD_REQUEST
            )

        schedule_type = request.data.get('schedule_type')
        if schedule_type not in ['regular', 'adhoc']:
            return Response(
                {"detail": "Invalid schedule type. Must be either 'regular' or 'adhoc'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determine appropriate models based on schedule type
        if schedule_type == 'regular':
            ScheduleModel = MaintenanceSchedule
            ConditionReportSerializer = ElevatorConditionReportSerializer
            MaintenanceLogSerializer = ScheduledMaintenanceLogSerializer
            schedule_field = 'maintenance_schedule'
        else:
            ScheduleModel = AdHocMaintenanceSchedule
            ConditionReportSerializer = AdHocElevatorConditionReportSerializer
            MaintenanceLogSerializer = AdHocMaintenanceLogSerializer
            schedule_field = 'ad_hoc_schedule'

        # Fetch and validate schedule
        maintenance_schedule = get_object_or_404(ScheduleModel, id=schedule_uuid)

        if not maintenance_schedule.technician:
            return Response({"detail": "No technician assigned."}, status=status.HTTP_400_BAD_REQUEST)
        if not maintenance_schedule.maintenance_company:
            return Response({"detail": "No maintenance company assigned."}, status=status.HTTP_400_BAD_REQUEST)
        if maintenance_schedule.status == 'completed':
            return Response({"detail": "Schedule already completed."}, status=status.HTTP_400_BAD_REQUEST)

        # Process condition report
        condition_report_data = request.data.get('condition_report', {})
        if not condition_report_data:
            return Response({"detail": "Condition report required."}, status=status.HTTP_400_BAD_REQUEST)

        condition_report_data.update({
            'technician': maintenance_schedule.technician.id,
            schedule_field: maintenance_schedule.id
        })

        condition_report_serializer = ConditionReportSerializer(data=condition_report_data)
        if not condition_report_serializer.is_valid():
            return Response({"detail": str(condition_report_serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        condition_report = condition_report_serializer.save()

        # Process maintenance log
        maintenance_log_data = request.data.get('maintenance_log', {})
        if not maintenance_log_data:
            return Response({"detail": "Maintenance log data required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate required fields based on schedule type
        if schedule_type == 'regular':
            checklist_fields = [
                'check_machine_gear', 'check_machine_brake', 'check_controller_connections',
                'blow_dust_from_controller', 'clean_machine_room', 'clean_guide_rails', 'observe_operation'
            ]
            missing_fields = [field for field in checklist_fields if field not in maintenance_log_data]
            if missing_fields:
                return Response(
                    {"detail": f"Missing required fields: {', '.join(missing_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif schedule_type == 'adhoc' and 'summary_title' not in maintenance_log_data:
            return Response(
                {"detail": "Summary title required for ad-hoc maintenance."},
                status=status.HTTP_400_BAD_REQUEST
            )

        maintenance_log_data.update({
            'technician': maintenance_schedule.technician.id,
            'condition_report': condition_report.id,
            schedule_field: maintenance_schedule.id,
            'date_completed': timezone.now()
        })

        # Create maintenance log
        maintenance_log_serializer = MaintenanceLogSerializer(data=maintenance_log_data)
        if not maintenance_log_serializer.is_valid():
            return Response({"detail": str(maintenance_log_serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        maintenance_log = maintenance_log_serializer.save()

        # Update schedule status based on scheduled date
        if maintenance_schedule.scheduled_date < timezone.now():
            maintenance_schedule.status = 'overdue'
        else:
            maintenance_schedule.status = 'completed'
        maintenance_schedule.save()

        # Create alert for developer approval
        try:
            developer = maintenance_schedule.elevator.building.developer
            elevator = maintenance_schedule.elevator
            
            # Create alert for developer approval
            AlertService.create_alert(
                alert_type=AlertType.MAINTENANCE_APPROVAL_NEEDED,
                recipient=developer,
                related_object=maintenance_schedule,
                message=(
                    f"Maintenance completed for elevator {elevator.machine_number} "
                    f"in building {elevator.building.name}. Please review and approve "
                    f"the maintenance log."
                )
            )

            # Create notification alert for maintenance company
            AlertService.create_alert(
                alert_type=AlertType.LOG_ADDED,
                recipient=maintenance_schedule.maintenance_company,
                related_object=maintenance_schedule,
                message=(
                    f"Maintenance log submitted for elevator {elevator.machine_number} "
                    f"in building {elevator.building.name}. Awaiting developer approval."
                )
            )

        except Exception as e:
            # Log the error but don't fail the request
            logger.error(f"Failed to create maintenance approval alert: {str(e)}")

        return Response(
            {"detail": f"{schedule_type.capitalize()} maintenance completed successfully and sent for approval."},
            status=status.HTTP_200_OK
        ) 
