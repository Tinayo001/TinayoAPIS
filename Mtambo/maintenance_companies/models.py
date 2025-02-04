import uuid
from django.db import models
from django.conf import settings

class MaintenanceCompanyProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='maintenance_profile'
    )
    company_name = models.CharField(max_length=255, default="Unnamed Company")
    company_address = models.CharField(max_length=255, default="Unknown Address")
    registration_number = models.CharField(max_length=255, default="DEFAULT_REG")
    specialization = models.CharField(max_length=255, default="Elevators")

    def __str__(self):
        return f"{self.company_name}"
