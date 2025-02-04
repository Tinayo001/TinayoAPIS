from django.db import models
from account.models import User
import uuid
from developers.models import DeveloperProfile
from maintenance_companies.models import MaintenanceCompanyProfile  # Import MaintenanceCompanyProfile

class Building(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    contact = models.CharField(max_length=255)
    developer = models.ForeignKey(
        DeveloperProfile, 
        on_delete=models.CASCADE, 
        related_name="buildings",
        null=False
    )
    developer_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True
    )

    def __str__(self):
        return f"{self.name} - {self.developer_name}"
