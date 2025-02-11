import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _


class AlertType(models.TextChoices):
    """
    Defines all possible alert types in the system
    """
    TECHNICIAN_SIGNUP = 'TECH_SIGNUP', _('Technician Signup')
    ELEVATOR_ASSIGNED = 'ELEVATOR_ASSIGNED', _('Elevator Assigned')
    SCHEDULE_ASSIGNED = 'SCHEDULE_ASSIGNED', _('Schedule Assigned')
    LOG_ADDED = 'LOG_ADDED', _('Maintenance Log Added')
    TASK_OVERDUE = 'TASK_OVERDUE', _('Task Overdue')
    TECHNICIAN_UNLINK = 'TECH_UNLINK', _('Technician Unlinked')
    ELEVATOR_REGISTERED = 'ELEVATOR_REG', _('Elevator Registered')
    BUILDING_REGISTERED = 'BUILDING_REG', _('Building Registered')
    SCHEDULE_OVERDUE = 'SCHEDULE_OVERDUE', _('Schedule Overdue') 
    ADHOC_MAINTENANCE_SCHEDULED = 'ADHOC_SCHEDULED', _('Ad-Hoc Maintenance Scheduled')


class Alert(models.Model):
    """
    Alert model for system notifications with generic relations to recipients and related objects
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    alert_type = models.CharField(
        max_length=50,
        choices=AlertType.choices,
        help_text=_("Type of alert being created")
    )
    message = models.TextField(
        help_text=_("Alert message content")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Timestamp when the alert was created")
    )
    is_read = models.BooleanField(
        default=False,
        help_text=_("Whether the alert has been read by the recipient")
    )
    
    # Generic relation to the recipient
    recipient_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='alert_recipients',
        help_text=_("Content type of the recipient")
    )
    recipient_id = models.UUIDField(
        help_text=_("UUID of the recipient object")
    )
    recipient = GenericForeignKey('recipient_type', 'recipient_id')
    
    # Generic relation to the related object
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='alert_content',
        help_text=_("Content type of the related object")
    )
    object_id = models.UUIDField(
        help_text=_("UUID of the related object")
    )
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient_type', 'recipient_id']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_read']),
        ]
        verbose_name = _("Alert")
        verbose_name_plural = _("Alerts")

    def __str__(self):
        return f"{self.alert_type} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"

    def mark_as_read(self):
        """Mark the alert as read"""
        self.is_read = True
        self.save(update_fields=['is_read'])

