from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from uuid import UUID
import logging

from .models import Alert
from .serializers import AlertSerializer

logger = logging.getLogger(__name__)


class AlertListView(generics.ListAPIView):
    """
    List all alerts for the authenticated user
    """
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Get content types for different user profiles
        developer_type = ContentType.objects.get(app_label='developers', model='developerprofile')
        company_type = ContentType.objects.get(app_label='maintenance_companies', model='maintenancecompanyprofile')
        technician_type = ContentType.objects.get(app_label='technicians', model='technicianprofile')
        
        query = Q()
        
        # Add queries based on user's profiles
        if hasattr(user, 'developer_profile'):
            query |= Q(recipient_type=developer_type, recipient_id=user.developer_profile.id)
        
        if hasattr(user, 'maintenance_company'):
            query |= Q(recipient_type=company_type, recipient_id=user.maintenance_company.id)
        
        if hasattr(user, 'technician_profile'):
            query |= Q(recipient_type=technician_type, recipient_id=user.technician_profile.id)
        
        alerts = Alert.objects.filter(query).order_by('-created_at')
        
        # Log query results for debugging
        logger.debug(f"Found {alerts.count()} alerts for user {user.id}")
        
        return alerts


class UnreadAlertsView(AlertListView):
    """
    List only unread alerts for the authenticated user
    """
    def get_queryset(self):
        return super().get_queryset().filter(is_read=False)


class MarkAlertReadView(generics.UpdateAPIView):
    """
    Mark a specific alert as read
    """
    queryset = Alert.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        try:
            alert = self.get_object()
            
            # Check if user has permission to mark this alert
            if not self._user_has_permission(request.user, alert):
                return Response(
                    {'error': 'You do not have permission to mark this alert as read'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            alert.mark_as_read()
            return Response({
                'status': 'success',
                'message': 'Alert marked as read successfully'
            })
            
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error marking alert as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark alert as read'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _user_has_permission(self, user, alert):
        """Check if user has permission to mark the alert as read"""
        recipient = alert.recipient
        
        if not recipient:
            return False
            
        # Check based on recipient type
        recipient_type = alert.recipient_type.model
        
        if recipient_type == 'developerprofile':
            return hasattr(user, 'developer_profile') and user.developer_profile.id == alert.recipient_id
        elif recipient_type == 'maintenancecompanyprofile':
            return hasattr(user, 'maintenance_company') and user.maintenance_company.id == alert.recipient_id
        elif recipient_type == 'technicianprofile':
            return hasattr(user, 'technician_profile') and user.technician_profile.id == alert.recipient_id
            
        return False


class MarkAllAlertsReadView(generics.GenericAPIView):
    """
    Mark all alerts as read for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get all unread alerts for the user
            alerts = AlertListView().get_queryset().filter(is_read=False)
            
            # Update all alerts
            count = alerts.update(is_read=True)
            
            return Response({
                'status': 'success',
                'message': f'Marked {count} alerts as read successfully'
            })
            
        except Exception as e:
            logger.error(f"Error marking all alerts as read: {str(e)}")
            return Response(
                {'error': 'Failed to mark alerts as read'},
                status=status.HTTP_400_BAD_REQUEST
            ) 
