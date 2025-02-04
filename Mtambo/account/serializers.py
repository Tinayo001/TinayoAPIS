from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from developers.models import DeveloperProfile
# User Serializer for account creation and validation
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['email', 'phone_number', 'first_name', 'last_name', 'password', 'account_type']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        # Extract profile-specific data
        account_type = validated_data.pop('account_type')
        
        # Create the user first
        user = get_user_model().objects.create_user(
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            account_type=account_type
        )

        # Create the corresponding profile based on account type
        if account_type == 'developer':
            DeveloperProfile.objects.create(
                user=user,
                developer_name=self.initial_data.get('developer_name'),
                address=self.initial_data.get('address')
            )
        elif account_type == 'maintenance':
            MaintenanceCompanyProfile.objects.create(
                user=user,
                company_name=self.initial_data.get('company_name'),
                company_address=self.initial_data.get('company_address'),
                registration_number=self.initial_data.get('registration_number'),
                specialization=self.initial_data.get('specialization')
        
            )
        elif account_type == 'technician':
            TechnicianProfile.objects.create(
                user=user,
                specialization=self.initial_data.get('specialization'),
                maintenance_company_id=self.initial_data.get('maintenance_company_id')
            )

        return user

# Login Serializer (For login purposes)
class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()  # Allow email or phone number as login identifier
    password = serializers.CharField()

class SpecializationSerializer(serializers.Serializer):
    key = serializers.CharField()  # For the dictionary key, like "option1"
    value = serializers.CharField()  # For the specialization value, like "Elevators"
