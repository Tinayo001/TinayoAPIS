from rest_framework import serializers
from buildings.models import Building
from .models import DeveloperProfile

class DeveloperProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeveloperProfile
        fields = ['developer_name', 'address']

    def update(self, instance, validated_data):
        instance.developer_name = validated_data.get('developer_name', instance.developer_name)
        instance.address = validated_data.get('address', instance.address)
        instance.save()
        return instance

class DeveloperListSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex_verbose', read_only=True)

    class Meta:
        model = DeveloperProfile
        fields = ['id', 'developer_name', 'address']
        extra_kwargs = {
            'id': {'read_only': True, 'format': 'hex_verbose'},
        }

class DeveloperDetailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(format='hex_verbose', read_only=True)
    buildings = serializers.SerializerMethodField()

    class Meta:
        model = DeveloperProfile
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True, 'format': 'hex_verbose'},
        }

    def get_buildings(self, obj):
        buildings = obj.buildings.all()  # This uses the related_name from your Building model
        return [
            {
                'id': str(building.id),  # Convert UUID to string
                'name': building.name,
                'address': building.address,
                'contact': building.contact
            }
            for building in buildings
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Ensure any UUID fields are properly converted to strings
        if 'id' in data:
            data['id'] = str(data['id'])
        return data

