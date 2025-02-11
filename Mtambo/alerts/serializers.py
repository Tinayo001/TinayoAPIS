from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    content_object_info = serializers.SerializerMethodField()
    recipient_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Alert
        fields = [
            'id', 
            'alert_type', 
            'message', 
            'created_at', 
            'is_read',
            'content_object_info',
            'recipient_info'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_content_object_info(self, obj):
        """Get information about the related object"""
        content_object = obj.content_object
        if not content_object:
            return None
            
        # Handle different content types
        content_type = obj.content_type.model
        
        try:
            if content_type == 'elevator':
                return {
                    'type': 'elevator',
                    'id': str(content_object.id),
                    'machine_number': content_object.machine_number,
                    'building': {
                        'id': str(content_object.building.id),
                        'name': content_object.building.name
                    }
                }
            elif content_type == 'building':
                return {
                    'type': 'building',
                    'id': str(content_object.id),
                    'name': content_object.name,
                    'address': content_object.address
                }
            elif content_type == 'maintenancelog':
                return {
                    'type': 'maintenance_log',
                    'id': str(content_object.id),
                    'elevator': {
                        'id': str(content_object.elevator.id),
                        'machine_number': content_object.elevator.machine_number
                    },
                    'date': content_object.date.isoformat()
                }
            
            return {
                'type': content_type,
                'id': str(content_object.id)
            }
        except Exception as e:
            return {
                'type': content_type,
                'id': str(obj.object_id),
                'error': 'Unable to fetch complete object details'
            }
    
    def get_recipient_info(self, obj):
        """Get information about the recipient"""
        recipient = obj.recipient
        if not recipient:
            return None
            
        try:
            recipient_type = obj.recipient_type.model
            
            if recipient_type == 'developerprofile':
                return {
                    'type': 'developer',
                    'id': str(recipient.id),
                    'name': recipient.developer_name,
                    'email': recipient.user.email
                }
            elif recipient_type == 'maintenancecompanyprofile':
                return {
                    'type': 'company',
                    'id': str(recipient.id),
                    'name': recipient.company_name,
                    'email': recipient.user.email
                }
            elif recipient_type == 'technicianprofile':
                return {
                    'type': 'technician',
                    'id': str(recipient.id),
                    'name': f"{recipient.user.first_name} {recipient.user.last_name}",
                    'email': recipient.user.email
                }
                
            return {
                'type': recipient_type,
                'id': str(recipient.id)
            }
        except Exception as e:
            return {
                'type': obj.recipient_type.model,
                'id': str(obj.recipient_id),
                'error': 'Unable to fetch complete recipient details'
            }
