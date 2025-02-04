from rest_framework import serializers
from account.models import User
from account.serializers import UserSerializer
from technicians.models import TechnicianProfile

# Serializer for listing all technicians (name, specialization, and company)

class TechnicianProfileSerializer(serializers.ModelSerializer):
    maintenance_company_id = serializers.IntegerField(write_only=True)  # Accept the ID for linking to Maintenance

    class Meta:
        model = TechnicianProfile
        fields = ['user', 'specialization', 'maintenance_company_id']

    def create(self, validated_data):
        maintenance_company_id = validated_data.pop('maintenance_company_id', None)

        if not maintenance_company_id:
            raise serializers.ValidationError("Maintenance company ID is required.")
        
        # Retrieve the maintenance company using the ID
        try:
            maintenance_company = Maintenance.objects.get(id=maintenance_company_id)
        except Maintenance.DoesNotExist:
            raise serializers.ValidationError("Maintenance company with the given ID does not exist.")
        
        # Create Technician instance and link it to the Maintenance company
        technician = Technician.objects.create(
            maintenance_company=maintenance_company, **validated_data
        )
        return technician


class TechnicianListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    technician_name = serializers.SerializerMethodField()
    id = serializers.UUIDField()  # Change from 'uuid' to 'id' as that's your primary key

    def get_technician_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    specialization = serializers.CharField()
    maintenance_company = serializers.CharField(source='maintenance_company.company_name', allow_null=True, required=False)

    class Meta:
        model = TechnicianProfile
        fields = ['id', 'user', 'technician_name', 'specialization', 'maintenance_company']

# Serializer for listing technicians by specialization
class TechnicianSpecializationSerializer(serializers.ModelSerializer):
    technician_name = serializers.SerializerMethodField()
    id = serializers.UUIDField()  # Change from 'uuid' to 'id'

    def get_technician_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    maintenance_company_name = serializers.CharField(source='maintenance_company.company_name', allow_null=True, required=False)

    class Meta:
        model = TechnicianProfile
        fields = ['id', 'technician_name', 'maintenance_company_name', 'specialization']

# Serializer for technician detailed view
class TechnicianDetailSerializer(serializers.ModelSerializer):
    technician_name = serializers.SerializerMethodField()
    id = serializers.UUIDField()  # Change from 'uuid' to 'id'

    def get_technician_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    maintenance_company_name = serializers.CharField(source='maintenance_company.company_name', allow_null=True, required=False)
    email = serializers.EmailField(source='user.email')
    phone_number = serializers.CharField(source='user.phone_number')

    class Meta:
        model = TechnicianProfile
        fields = ['id', 'technician_name', 'specialization', 'maintenance_company_name', 'email', 'phone_number']


