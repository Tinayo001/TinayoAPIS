from django.db import models
from django.conf import settings
import uuid
from account.models import User

class DeveloperProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='developer_profile',
        null=True,  # Allow null if there's no user set initially
        blank=True  # Allow blank if the user field is empty
    )
    developer_name = models.CharField(max_length=100, default='Unknown Developer')  # Optional default
    address = models.TextField(default='Not provided') 
    specialization = models.CharField(max_length=255, default="Elevators")

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.specialization}"  

