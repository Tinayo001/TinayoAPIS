from rest_framework import serializers
import uuid
from .models import Building
from account.models import User
from developers.models import DeveloperProfile
from elevators.serializers import ElevatorReadSerializer
from elevators.serializers import ElevatorSerializer

class AddBuildingRequestSerializer(serializers.Serializer):
    developer_id = serializers.UUIDField(required=True, help_text="The UUID of the developer.")
    name = serializers.CharField(max_length=255, required=True, help_text="Name of the building.")
    address = serializers.CharField(max_length=255, required=True, help_text="Address of the building.")
    developer_name = serializers.CharField(max_length=255, required=True, help_text="The name of the developer.")
    contact = serializers.CharField(max_length=255, required=True, help_text="The contact information of the developer.")

    def validate_developer(self, value):
        """ Custom validation for the developer_id field to check if it's a valid UUID """
        if not isinstance(value.id, uuid.UUID):  # Ensure uuid.UUID is being used correctly
            raise serializers.ValidationError("Invalid developer ID format.")
        return value

class BuildingSerializer(serializers.ModelSerializer):
    elevators = ElevatorSerializer(many=True, read_only=True)
    developer = serializers.PrimaryKeyRelatedField(
        queryset=DeveloperProfile.objects.all(),
        pk_field=serializers.UUIDField(format='hex_verbose')
    )
    developer_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Building
        fields = ['id', 'name', 'address', 'contact', 'developer', 'developer_name', 'elevators']
        extra_kwargs = {
            'id': {'read_only': True, 'format': 'hex_verbose'},
        }

    def create(self, validated_data):
        developer = validated_data.get('developer')
        developer_name = validated_data.get('developer_name') or developer.developer_name
        validated_data['developer_name'] = developer_name
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['developer'] = {
            'id': str(instance.developer.id),  # Convert UUID to string
            'developer_name': instance.developer.developer_name
        }
        return data

    def validate_developer(self, value):
        if not isinstance(value.id, uuid.UUID):
            try:
                uuid.UUID(str(value.id))
            except (ValueError, TypeError, AttributeError):
                raise serializers.ValidationError("Invalid developer ID format")
        return value

