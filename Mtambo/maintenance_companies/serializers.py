from rest_framework import serializers
from account.models import User
from technicians.models import TechnicianProfile
from .models import MaintenanceCompanyProfile
from elevators.models import Elevator
from elevators.serializers import ElevatorSerializer

class MaintenanceCompanyProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the MaintenanceCompanyProfile model. 
    Handles both creation and updating of maintenance company profiles.
    """
    class Meta:
        model = MaintenanceCompanyProfile
        fields = ['id', 'user', 'company_name', 'company_address', 'registration_number', 'specialization']
    
    def validate(self, data):
        """
        Ensure that the company name is provided.
        """
        if not data.get('company_name'):
            raise serializers.ValidationError({
                'company_name': 'This field is required.'
            })
        return data
    
    def update(self, instance, validated_data):
        """
        Update the MaintenanceCompanyProfile instance with validated data.
        """
        # Ensure that we update the fields that are in the validated data
        for key, value in validated_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        # Save the instance after updating fields
        instance.save()
        return instance

class AddBuildingSerializer(serializers.Serializer):
    developer_uuid = serializers.UUIDField(help_text="UUID of the developer")
    name = serializers.CharField(max_length=255, help_text="Name of the building")
    address = serializers.CharField(max_length=255, help_text="Address of the building")
    contact = serializers.CharField(max_length=255, help_text="Contact information")
    elevators = serializers.ListField(  # Changed from elevator to elevators
        child=ElevatorSerializer(),
        help_text="List of elevators to be added to the building",
        required=True
    )

    def validate_elevators(self, value):
        """
        Validate the elevators list.
        """
        if not value:
            raise serializers.ValidationError("At least one elevator is required.")
        
        for elevator in value:
            if not isinstance(elevator.get('capacity'), int):
                raise serializers.ValidationError({"capacity": "A valid integer is required."})
        
        return value

class MaintenanceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceCompanyProfile
        fields = ['id', 'company_name']
