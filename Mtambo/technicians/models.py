import uuid
from django.db import models
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile


class TechnicianProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='technician_profile',
        default=None
    )
    specialization = models.CharField(max_length=100, default="Unknown")
    maintenance_company = models.ForeignKey(
        MaintenanceCompanyProfile, 
        on_delete=models.CASCADE, 
        related_name='technicians', 
        null=True, 
        blank=True
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.maintenance_company or 'Unlinked'}"

    class Meta:
        ordering = ['-created_at']

