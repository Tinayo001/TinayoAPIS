from rest_framework import serializers
from .models import BrokerUser
import uuid

class BrokerRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for broker registration.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = BrokerUser
        fields = [
            'first_name', 'last_name', 'email', 'phone_number',
            'password', 'confirm_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True},
        }

    def validate(self, data):
        """
        Validate that the password and confirm_password match.
        """
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """
        Create a new broker user with auto-generated referral_code and default commission values.
        """
        validated_data.pop('confirm_password')  # Remove confirm_password from the data

        # Auto-generate a unique referral_code (8 characters)
        validated_data['referral_code'] = str(uuid.uuid4())[:8].upper()  # Generate the referral code

        # Set default commission values
        validated_data['commission_percentage'] = 12.5  # Default commission percentage
        validated_data['commission_duration_months'] = 24  # Default commission duration

        # Create the user with the generated referral code
        user = BrokerUser.objects.create_user(
            referral_code=validated_data['referral_code'],  # Use the referral code as the unique identifier
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            commission_percentage=validated_data['commission_percentage'],
            commission_duration_months=validated_data['commission_duration_months'],
        )
        return user
    
    def to_representation(self, instance):
        """
        Exclude password from the response and include all required fields such as id, referral_code, etc.
        """
        representation = super().to_representation(instance)
        representation.pop('password', None)  # Ensure password is not returned
        representation['id'] = instance.id  # Add the 'id' of the broker
        representation['referral_code'] = instance.referral_code  # Include the referral code
        representation['commission_percentage'] = instance.commission_percentage  # Include commission percentage
        representation['commission_duration_months'] = instance.commission_duration_months  # Include commission duration
        return representation
