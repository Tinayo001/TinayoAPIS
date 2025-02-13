from datetime import date
from django.db import models
from buildings.models import Building
from account.models import User
from developers.models import DeveloperProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
import uuid

class Elevator(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user_name = models.CharField(
        max_length=100,
        unique=False,
        help_text="Identifier for the elevator (e.g., LIFT1, LIFT2)."
    )
    controller_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Specify the type of controller (e.g., Digital, Analog, etc.)."
    )
    machine_type = models.CharField(
        max_length=100,
        choices=[('gearless', 'Gearless'), ('geared', 'Geared')],
        default='gearless',
        help_text="Type of the elevator machine (e.g., Gearless, Geared)."
    )
    building = models.ForeignKey(
        Building, 
        on_delete=models.CASCADE, 
        related_name="elevators"
    )
    machine_number = models.CharField(
        max_length=100, 
        unique=True
    )
    capacity = models.PositiveIntegerField(
        help_text="Maximum weight capacity in kilograms."
    )
    manufacturer = models.CharField(max_length=255)
    installation_date = models.DateField()

    # Maintenance Company relationship
    maintenance_company = models.ForeignKey(
        MaintenanceCompanyProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="elevators"
    )

    # Developer relationship
    developer = models.ForeignKey(
        DeveloperProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="developed_elevators"
    )

    # Technician relationship
    technician = models.ForeignKey(
        TechnicianProfile, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="assigned_elevators"
    )
    class Meta:
        ordering = ['machine_number']
        indexes = [
            models.Index(fields=['machine_number']),
            models.Index(fields=['installation_date']),
        ]
    def str(self):
        return f"{self.machine_number} - {self.user_name} - {self.building.name}"

class ElevatorIssueLog(models.Model):
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE, related_name="issue_logs")
    developer = models.ForeignKey(DeveloperProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="reported_issues")
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="elevator_issue_logs")
    reported_date = models.DateTimeField(auto_now_add=True, help_text="The date and time when the issue was reported.")
    issue_description = models.TextField(help_text="A detailed description of the elevator issue reported by the developer.")

    def __str__(self):
        return f"Issue reported for Elevator: {self.elevator.user_name} in Building: {self.building.name} on {self.reported_date.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = "Elevator Issue Log"
        verbose_name_plural = "Elevator Issue Logs"
        ordering = ['-reported_date']
