from uuid import UUID
from rest_framework import serializers
from .models import Elevator
from buildings.models import Building
from django.shortcuts import get_object_or_404
from .models import ElevatorIssueLog
from technicians.models import TechnicianProfile 

class ElevatorSerializer(serializers.ModelSerializer):
    """Base serializer for Elevator model with common fields and validations."""
    
    class Meta:
        model = Elevator
        fields = [
            'id', 
            'user_name',
            'controller_type',
            'machine_type',
            'machine_number',
            'capacity',
            'manufacturer',
            'installation_date',
        ]

    def validate_machine_number(self, value):
        """Validate machine number uniqueness."""
        elevator_instance = self.instance
        query = Elevator.objects.filter(machine_number=value)
        
        if elevator_instance:
            query = query.exclude(id=elevator_instance.id)
            
        if query.exists():
            raise serializers.ValidationError(
                "An elevator with this machine number already exists."
            )
        return value

    def validate_user_name(self, value):
        """Validate username uniqueness within a building."""
        building = self.context.get('building')
        if not building:
            return value
            
        query = Elevator.objects.filter(user_name=value, building=building)
        
        if self.instance:
            query = query.exclude(id=self.instance.id)
            
        if query.exists():
            raise serializers.ValidationError(
                f"A user name '{value}' already exists in this building."
            )
        return value

class ElevatorReadSerializer(ElevatorSerializer):
    """Serializer for reading elevator details with related fields."""
    
    maintenance_company = serializers.SerializerMethodField()
    technician = serializers.SerializerMethodField()
    developer = serializers.SerializerMethodField()
    building = serializers.SerializerMethodField()

    class Meta(ElevatorSerializer.Meta):
        fields = ElevatorSerializer.Meta.fields + [
            'maintenance_company',
            'technician',
            'developer',
            'building'
        ]

    def get_maintenance_company(self, obj):
        if obj.maintenance_company:
            return {
                'id': obj.maintenance_company.id,
                'name': obj.maintenance_company.company_name
            }
        return None

    def get_technician(self, obj):
        if obj.technician:
            return {
                'id': obj.technician.id,
                'name': f"{obj.technician.user.first_name} {obj.technician.user.last_name}"
            }
        return None

    def get_developer(self, obj):
        if obj.developer:
            return {
                'id': obj.developer.id,
                'name': obj.developer.developer_name
            }
        return None

    def get_building(self, obj):
        print(f"Elevator ID: {obj.id} | Building: {obj.building}") 
        if obj.building:
            return {
                'id': obj.building.id,
                'name': obj.building.name
            }
        print(f"Building not found for elevator {obj.id}") 
        return None

class ElevatorCreateSerializer(serializers.Serializer):
    user_name = serializers.CharField(
        required=True,
        help_text="Identifier for the elevator (e.g., LIFT1, LIFT2)."
    )
    machine_number = serializers.CharField(
        required=True,
        help_text="Unique identifier for the elevator machine."
    )
    capacity = serializers.IntegerField(
        required=True,
        help_text="Maximum weight capacity in kilograms."
    )
    manufacturer = serializers.CharField(
        required=True,
        help_text="Name of the elevator manufacturer."
    )
    installation_date = serializers.DateField(
        required=True,
        help_text="Date of installation (YYYY-MM-DD)."
    )
    building = serializers.UUIDField(
        required=True,
        help_text="UUID of the building where the elevator is installed."
    )
    technician = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="UUID of the assigned technician (optional)."
    )
    controller_type = serializers.CharField(
        required=False,
        help_text="Type of the elevator controller (optional)."
    )
    machine_type = serializers.CharField(
        required=False,
        help_text="Type of the elevator machine (optional)."
    )

    def validate_machine_number(self, value):
        """Ensure unique machine number."""
        if Elevator.objects.filter(machine_number=value).exists():
            raise serializers.ValidationError("An elevator with this machine number already exists.")
        return value

    def validate_user_name(self, value):
        """Ensure unique user name within the building."""
        building_id = self.initial_data.get('building')
        if building_id:
            building = get_object_or_404(Building, id=building_id)
            if Elevator.objects.filter(user_name=value, building=building).exists():
                raise serializers.ValidationError("A user name already exists in this building.")
        return value

    def create(self, validated_data):
        """Create an Elevator instance."""
        building_id = validated_data.pop('building')
        technician_id = validated_data.pop('technician', None)

        building = get_object_or_404(Building, id=building_id)
        technician = None
        if technician_id:
            technician = get_object_or_404(TechnicianProfile, id=technician_id)

        elevator = Elevator.objects.create(
            building=building,
            technician=technician,
            **validated_data
        )
        return elevator

class ElevatorIssueLogSerializer(serializers.ModelSerializer):
    building_name = serializers.CharField(source='building.name', read_only=True)
    elevator_username = serializers.CharField(source='elevator.user_name', read_only=True)
    elevator_machine_number = serializers.CharField(source='elevator.machine_number', read_only=True)
    issue_id = serializers.IntegerField(source='id', read_only=True)

    class Meta:
        model = ElevatorIssueLog
        fields = ['issue_id', 'elevator', 'developer', 'building', 'reported_date', 'issue_description', 'building_name', 'elevator_username', 'elevator_machine_number']

    def create(self, validated_data):
        # Automatically fill elevator, developer, and building from the elevator instance
        elevator = validated_data['elevator']
        developer = elevator.developer  # Assuming the elevator has a linked developer
        building = elevator.building  # Assuming the elevator is linked to a building

        issue_log = ElevatorIssueLog.objects.create(
            elevator=elevator,
            developer=developer,
            building=building,
            issue_description=validated_data['issue_description']
        )
        return issue_log
