from rest_framework import serializers
from elevators.models import Elevator
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from .models import *
from rest_framework.exceptions import ValidationError
from .utils import update_schedule_status_and_create_new_schedule
from elevators.serializers import ElevatorSerializer

class BuildingScheduleCompletionSerializer(serializers.Serializer):
    elevators = serializers.ListField(
        child=ElevatorSerializer(),
        required=True
    )

class BaseScheduleSerializer(serializers.ModelSerializer):
    """
    A base serializer to provide common fields for both MaintenanceSchedule and AdHocMaintenanceSchedule.
    """
    schedule_type = serializers.SerializerMethodField()

    def get_schedule_type(self, obj):
        return "normal" if isinstance(obj, MaintenanceSchedule) else "adhoc"

class AdhocScheduleCreateSerializer(serializers.Serializer):
    description = serializers.CharField(required=True)

    def validate_description(self, value):
        """Ensure description is required and not empty."""
        if not value.strip():
            raise serializers.ValidationError("Description cannot be empty.")
        return value

class MaintenanceScheduleSerializer(serializers.ModelSerializer):
    elevator = serializers.PrimaryKeyRelatedField(queryset=Elevator.objects.all())
    technician = serializers.PrimaryKeyRelatedField(queryset=TechnicianProfile.objects.all(), required=False, allow_null=True)
    maintenance_company = serializers.PrimaryKeyRelatedField(queryset=MaintenanceCompanyProfile.objects.all(), required=False, allow_null=True)

    class Meta:
        model = MaintenanceSchedule
        fields = ['id', 'elevator', 'technician', 'maintenance_company', 'scheduled_date', 'next_schedule', 'description', 'status']

        read_only_fields = ['maintenance_company', 'technician'] 

    def validate(self, data):
        elevator = data.get('elevator')
        technician = data.get('technician')
        maintenance_company = data.get('maintenance_company')

        # If technician is provided, it should belong to the same maintenance company as the elevator
        if technician:
            if technician.maintenance_company != elevator.maintenance_company:
                raise ValidationError("Technician does not belong to the same maintenance company as the elevator.")
        elif not technician:
            # Auto-assign technician if not provided, or leave as NULL
            technician = elevator.technician if elevator.technician else None
            data['technician'] = technician

        # Set the maintenance company from the elevator if not provided
        if not maintenance_company:
            maintenance_company = elevator.maintenance_company
        data['maintenance_company'] = maintenance_company

        return data

    def create(self, validated_data):
        # When creating the schedule, use the validated data directly
        elevator = validated_data['elevator']
        technician = validated_data.get('technician', elevator.technician)  # Use elevator technician if not provided
        maintenance_company = validated_data['maintenance_company']

        schedule = MaintenanceSchedule.objects.create(
            elevator=elevator,
            technician=technician,
            maintenance_company=maintenance_company,
            scheduled_date=validated_data['scheduled_date'],
            next_schedule=validated_data.get('next_schedule', 'set_date'),
            description=validated_data.get('description', ''),
            status=validated_data.get('status', 'scheduled')
        )

        return schedule

    def to_representation(self, instance):
        # Convert related objects to their IDs instead of full objects
        representation = super().to_representation(instance)
        representation['elevator'] = str(instance.elevator.id)  # Convert UUID to string
        representation['technician'] = str(instance.technician.id) if instance.technician else None
        representation['maintenance_company'] = str(instance.maintenance_company.id) if instance.maintenance_company else None
        return representation


class MaintenanceScheduleStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=MaintenanceSchedule.STATUS_CHOICES)  # Only allow valid statuses

    class Meta:
        model = MaintenanceSchedule
        fields = ['status']  # Only allow updating the status field

    def update(self, instance, validated_data):
        """
        Updates the status of the maintenance schedule and triggers the creation of a new schedule if required.
        """
        # Update the status first
        instance.status = validated_data.get('status', instance.status)

        # Call the helper function to update the status and possibly create a new schedule
        update_schedule_status_and_create_new_schedule(instance)

        # Save the instance after status update and any necessary schedule creation
        instance.save()

        return instance


class FullMaintenanceScheduleSerializer(serializers.ModelSerializer):
    elevator = serializers.PrimaryKeyRelatedField(queryset=Elevator.objects.all())
    building = serializers.SerializerMethodField()
    developer = serializers.SerializerMethodField()

    class Meta:
        model = MaintenanceSchedule
        fields = ['id', 'elevator', 'technician', 'maintenance_company', 'scheduled_date', 'next_schedule', 'description', 'status', 'building', 'developer']

    def get_building(self, obj):
        # Get the building linked to the elevator
        building = obj.elevator.building  # Assuming `Elevator` has a `building` field
        return {'id': str(building.id), 'name': building.name} if building else None  # Convert UUID to string

    def get_developer(self, obj):
        # Get the developer linked to the building
        building = obj.elevator.building
        developer = building.developer if building else None
        return {'id': str(developer.id), 'name': developer.developer_name} if developer else None  # Convert UUID to string


class AdHocMaintenanceScheduleSerializer(BaseScheduleSerializer):
    """
    Serializer for the Ad-Hoc Maintenance Schedule.
    """
    class Meta:
        model = AdHocMaintenanceSchedule
        fields = [
            'id',
            'schedule_type',
            'elevator',
            'technician',
            'maintenance_company',
            'scheduled_date',
            'description',
            'status',
        ]

        read_only_fields = ['technician'] 


class ElevatorConditionReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElevatorConditionReport
        fields = [
            'id',
            'maintenance_schedule',
            'technician',
            'date_inspected',
            'alarm_bell',
            'noise_during_motion',
            'cabin_lights',
            'position_indicators',
            'hall_lantern_indicators',
            'cabin_flooring',
            'additional_comments',
        ]


class ScheduledMaintenanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduledMaintenanceLog
        fields = [
            'id',
            'maintenance_schedule',
            'technician',
            'condition_report',
            'date_completed',
            'check_machine_gear',
            'check_machine_brake',
            'check_controller_connections',
            'blow_dust_from_controller',
            'clean_machine_room',
            'clean_guide_rails',
            'observe_operation',
            'description',
            'overseen_by',
            'approved_by',
        ]


class AdHocElevatorConditionReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdHocElevatorConditionReport
        fields = ['id', 'ad_hoc_schedule', 'technician', 'date_inspected', 'components_checked', 'condition']


class AdHocMaintenanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdHocMaintenanceLog
        fields = [
            'id', 'ad_hoc_schedule', 'technician', 'condition_report', 'date_completed',
            'summary_title', 'description', 'overseen_by', 'approved_by'
        ]


class CompleteMaintenanceScheduleSerializer(BaseScheduleSerializer):
    """
    Serializer for handling both normal and ad-hoc maintenance schedules with nested reports and logs.
    """
    elevator = serializers.SerializerMethodField()
    building = serializers.SerializerMethodField()
    developer = serializers.SerializerMethodField()
    technician_full_name = serializers.SerializerMethodField()
    maintenance_company_name = serializers.SerializerMethodField()
    condition_report = serializers.SerializerMethodField()
    maintenance_log = serializers.SerializerMethodField()
    elevator_details = serializers.SerializerMethodField()  # New field for elevator details

    class Meta:
        model = MaintenanceSchedule
        fields = [
            'id',
            'schedule_type',
            'elevator',
            'elevator_details',  # Include elevator details in fields
            'technician',
            'technician_full_name',
            'maintenance_company',
            'maintenance_company_name',
            'scheduled_date',
            'description',
            'status',
            'building',
            'developer',
            'condition_report',
            'maintenance_log',
        ]

    def get_building(self, obj):
        building = obj.elevator.building
        return {'id': str(building.id), 'name': building.name} if building else None  # Convert UUID to string

    def get_developer(self, obj):
        building = obj.elevator.building
        developer = building.developer if building else None
        return {'id': str(developer.id), 'name': developer.developer_name} if developer else None  # Convert UUID to string

    def get_technician_full_name(self, obj):
        technician = obj.technician
        return f"{technician.user.first_name} {technician.user.last_name}" if technician else None

    def get_maintenance_company_name(self, obj):
        maintenance_company = obj.maintenance_company
        return maintenance_company.company_name if maintenance_company else None

    def get_condition_report(self, obj):
        """
        Returns the associated condition report for the schedule.
        Handles both normal and ad-hoc schedules.
        """
        if isinstance(obj, MaintenanceSchedule):
            reports = ElevatorConditionReport.objects.filter(maintenance_schedule=obj)
            serializer = ElevatorConditionReportSerializer(reports, many=True)
        else:
            reports = AdHocElevatorConditionReport.objects.filter(ad_hoc_schedule=obj)
            serializer = AdHocElevatorConditionReportSerializer(reports, many=True)
        return serializer.data

    def get_maintenance_log(self, obj):
        """
        Returns the associated maintenance log for the schedule.
        Handles both normal and ad-hoc schedules.
        """
        if isinstance(obj, MaintenanceSchedule):
            logs = ScheduledMaintenanceLog.objects.filter(maintenance_schedule=obj)
            serializer = ScheduledMaintenanceLogSerializer(logs, many=True)
        else:
            logs = AdHocMaintenanceLog.objects.filter(ad_hoc_schedule=obj)
            serializer = AdHocMaintenanceLogSerializer(logs, many=True)
        return serializer.data

    def get_elevator_details(self, obj):
        """
        Returns the elevator details, including user_name and machine_number.
        """
        elevator = obj.elevator
        if elevator:
            return {
                'id': str(elevator.id),  # Convert UUID to string
                'user_name': elevator.user_name,
                'machine_number': elevator.machine_number
            }
        return None

    def get_elevator(self, obj):
        # Check if the instance has an 'elevator' attribute
        if hasattr(obj, 'elevator'):
            return ElevatorSerializer(obj.elevator).data
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Organize the response structure
        result = {
            'maintenance_schedule': {
                'id': data['id'],
                'schedule_type': data['schedule_type'],
                'elevator': data.get('elevator_details', None),  # Add elevator details here
                'technician': data['technician'],
                'technician_full_name': data['technician_full_name'],
                'maintenance_company': data['maintenance_company'],
                'maintenance_company_name': data['maintenance_company_name'],
                'scheduled_date': data['scheduled_date'],
                'description': data['description'],
                'status': data['status'],
                'building': data['building'],
                'developer': data['developer'],
                'condition_report': data.get('condition_report', None),
                'maintenance_log': data.get('maintenance_log', None),
            }
        }

        return result

class BuildingLevelAdhocScheduleSerializer(serializers.ModelSerializer):
    building_name = serializers.SerializerMethodField()
    technician_name = serializers.SerializerMethodField()
    elevators = serializers.SerializerMethodField()
    developer = serializers.SerializerMethodField()

    class Meta:
        model = BuildingLevelAdhocSchedule
        fields = [
            'id',
            'building',
            'building_name',
            'technician',
            'technician_name',
            'maintenance_company',
            'scheduled_date',
            'description',
            'status',
            'elevators',
            'developer'
        ]
        read_only_fields = [
            'building_name',
            'technician_name',
            'elevators',
            'developer'
        ]

    def get_building_name(self, obj):
        """Retrieve the name of the building."""
        return obj.building.name if obj.building else None

    def get_technician_name(self, obj):
        """Retrieve the name of the technician."""
        return f"{obj.technician.user.first_name} {obj.technician.user.last_name}" if obj.technician else None

    def get_elevators(self, obj):
        """Retrieve all elevators in the building with their usernames and IDs."""
        if not obj.building:
            return []
        elevators = Elevator.objects.filter(building=obj.building)
        return [
            {
                "id": str(elevator.id),  # Convert UUID to string
                "username": elevator.user_name,
                "machine_number": elevator.machine_number
            }
            for elevator in elevators
        ]
    def get_developer(self, obj):
        """Retrieve the developer details for the building."""
        building = obj.building
        developer = building.developer if building else None
        return {'id': str(developer.id), 'name': developer.developer_name} if developer else None
