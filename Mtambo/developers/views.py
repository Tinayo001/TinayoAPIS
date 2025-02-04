from uuid import UUID
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from .models import DeveloperProfile
from .serializers import DeveloperListSerializer, DeveloperDetailSerializer
from rest_framework.views import APIView
import uuid
from rest_framework.exceptions import NotFound, ValidationError
from jobs.models import *
from jobs.serializers import CompleteMaintenanceScheduleSerializer
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404


import logging
logger = logging.getLogger(__name__)

from rest_framework.exceptions import NotFound, ValidationError

class DeveloperDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = DeveloperDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return DeveloperProfile.objects.all()

    def get_object(self):
        developer_id = self.kwargs['developer_id']  # This should be a UUID string
    
        try:
            developer = DeveloperProfile.objects.get(id=developer_id)  # Retrieve the developer using the UUID directly
            return developer
        except DeveloperProfile.DoesNotExist:
            raise NotFound(detail="Developer not found", code=404)
        except ValueError:
            raise ValidationError(detail="Invalid developer ID format", code=400)

class DeveloperDetailByEmailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = DeveloperDetailSerializer
    lookup_field = 'user__email'

    def get_queryset(self):
        return DeveloperProfile.objects.all()

    def get_object(self):
        try:
            return DeveloperProfile.objects.get(user__email=self.kwargs['developer_email'])
        except DeveloperProfile.DoesNotExist:
            raise NotFound(detail="Developer with this email not found.", code=404)

class DeveloperMaintenanceLogApprovalView(APIView):
    permission_classes = [AllowAny]  # Replace with appropriate permissions

    def get(self, request, developer_uuid):
        # [Keep your GET method as before...]
        try:
            developer = get_object_or_404(DeveloperProfile, id=developer_uuid)
            regular_logs_queryset = ScheduledMaintenanceLog.objects.filter(approved_by__isnull=True)
            adhoc_logs_queryset = AdHocMaintenanceLog.objects.filter(approved_by__isnull=True)
            regular_schedules = MaintenanceSchedule.objects.filter(
                elevator__building__developer=developer,
                status="completed"
            ).prefetch_related(
                Prefetch('maintenance_logs', queryset=regular_logs_queryset, to_attr='unapproved_maintenance_logs'),
                'unapproved_maintenance_logs__condition_report',
            )
            adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(
                elevator__building__developer=developer,
                status="completed"
            ).prefetch_related(
                Prefetch('maintenance_logs', queryset=adhoc_logs_queryset, to_attr='unapproved_maintenance_logs'),
                'unapproved_maintenance_logs__condition_report',
            )
            filtered_regular_schedules = [
                schedule for schedule in regular_schedules if schedule.unapproved_maintenance_logs
            ]
            filtered_adhoc_schedules = [
                schedule for schedule in adhoc_schedules if schedule.unapproved_maintenance_logs
            ]
            regular_data = CompleteMaintenanceScheduleSerializer(filtered_regular_schedules, many=True).data
            adhoc_data = CompleteMaintenanceScheduleSerializer(filtered_adhoc_schedules, many=True).data

            if not regular_data and not adhoc_data:
                return Response(
                    {"detail": "No pending unapproved maintenance logs for this developer."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "unapproved_regular_schedules": regular_data,
                    "unapproved_adhoc_schedules": adhoc_data,
                },
                status=status.HTTP_200_OK,
            )
        except DeveloperProfile.DoesNotExist:
            return Response({"detail": "Developer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"detail": "An unexpected error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Approve maintenance logs for a developer",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'regular_maintenance_log_uuids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, description='UUID of regular maintenance log'),
                    description='List of regular maintenance log UUIDs to approve'
                ),
                'adhoc_maintenance_log_uuids': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING, description='UUID of ad-hoc maintenance log'),
                    description='List of ad-hoc maintenance log UUIDs to approve'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description='Maintenance logs approval status',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'successful_approvals': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'uuid': openapi.Schema(type=openapi.TYPE_STRING),
                                    'type': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        ),
                        'not_found': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'uuid': openapi.Schema(type=openapi.TYPE_STRING),
                                    'type': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        ),
                        'already_approved': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'uuid': openapi.Schema(type=openapi.TYPE_STRING),
                                    'type': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            404: openapi.Response(description='No valid maintenance logs found'),
            403: openapi.Response(description='Forbidden - Log does not belong to developer'),
            500: openapi.Response(description='Internal server error')
        }
    )
    def put(self, request, developer_uuid):
        try:
            developer = get_object_or_404(DeveloperProfile, id=developer_uuid)
            regular_log_uuids = request.data.get("regular_maintenance_log_uuids", [])
            adhoc_log_uuids = request.data.get("adhoc_maintenance_log_uuids", [])
            successful_approvals = []
            not_found = []
            already_approved = []

            # Helper: process logs and return a Response if an error occurs.
            def process_logs(log_uuids, log_model, log_type):
                if not log_uuids:
                    return None

                logs = log_model.objects.filter(id__in=log_uuids)
                for log_uuid in log_uuids:
                    log = logs.filter(id=log_uuid).first()
                    if not log:
                        not_found.append({"uuid": log_uuid, "type": log_type})
                        continue

                    if log.approved_by:
                        already_approved.append({"uuid": log_uuid, "type": log_type})
                        continue

                    # Check if the log belongs to the developer.
                    if log_type == "regular":
                        if log.maintenance_schedule.elevator.building.developer != developer:
                            return Response(
                                {"detail": f"Log {log_uuid} ({log_type}) does not belong to the specified developer."},
                                status=status.HTTP_403_FORBIDDEN
                            )
                    elif log_type == "adhoc":
                        if log.ad_hoc_schedule.elevator.building.developer != developer:
                            return Response(
                                {"detail": f"Log {log_uuid} ({log_type}) does not belong to the specified developer."},
                                status=status.HTTP_403_FORBIDDEN
                            )

                    log.approved_by = developer.developer_name
                    log.save()
                    successful_approvals.append({"uuid": log_uuid, "type": log_type})
                return None

            # Process each log type; if an error Response is returned, exit immediately.
            resp = process_logs(regular_log_uuids, ScheduledMaintenanceLog, "regular")
            if resp is not None:
                return resp
            resp = process_logs(adhoc_log_uuids, AdHocMaintenanceLog, "adhoc")
            if resp is not None:
                return resp

            response_data = {
                "successful_approvals": successful_approvals,
                "not_found": not_found,
                "already_approved": already_approved
            }

            if not successful_approvals and not_found:
                return Response(
                    {"detail": "No valid maintenance logs found.", "data": response_data},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(response_data, status=status.HTTP_200_OK)

        except DeveloperProfile.DoesNotExist:
            return Response({"detail": "Developer not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(
                {"detail": "An unexpected error occurred.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

