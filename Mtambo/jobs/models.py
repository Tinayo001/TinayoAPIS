from datetime import datetime
from django.db import models, IntegrityError
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import uuid

from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
from buildings.models import Building
from .utils import update_schedule_status_and_create_new_schedule

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

import logging

from django.utils.timezone import now


logger = logging.getLogger(__name__)

class MaintenanceSchedule(models.Model):
    SCHEDULE_CHOICES = [
        ('1_month', '1 Month'),
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('set_date', 'Set Date'),
    ]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('overdue', 'Overdue'),
        ('completed', 'Completed')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elevator = models.ForeignKey(
        Elevator,  # Changed from 'Elevator' to Elevator
        on_delete=models.CASCADE, 
        related_name="maintenance_schedules"
    )
    technician = models.ForeignKey(
        TechnicianProfile,  # Changed from 'TechnicianProfile' to TechnicianProfile
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="maintenance_schedules"
    )
    maintenance_company = models.ForeignKey(
        MaintenanceCompanyProfile,  # Changed from 'MaintenanceCompanyProfile' to MaintenanceCompanyProfile
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="maintenance_schedules"
    )
    scheduled_date = models.DateTimeField()
    next_schedule = models.CharField(
        max_length=10, 
        choices=SCHEDULE_CHOICES, 
        default='set_date'
    )
    description = models.TextField()
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='scheduled'
    )

    class Meta:
        unique_together = ['elevator', 'scheduled_date']
        ordering = ['-scheduled_date']
        verbose_name = "Maintenance Schedule"
        verbose_name_plural = "Maintenance Schedules"

    def __str__(self):
        scheduled_date_str = self.scheduled_date.strftime('%Y-%m-%d %H:%M:%S')
        technician_name = (f"{self.technician.user.first_name} {self.technician.user.last_name}"
                             if self.technician else 'No Technician Assigned')
        maintenance_company_name = (self.maintenance_company.company_name 
                                    if self.maintenance_company else 'No Company Assigned')
        return (f"Scheduled: {scheduled_date_str} | Maintenance Company: {maintenance_company_name} | "
                f"Technician: {technician_name} | Status: {self.status}")

    def save(self, *args, **kwargs):
        # Convert scheduled_date if provided as a string
        if isinstance(self.scheduled_date, str):
            self.scheduled_date = datetime.fromisoformat(self.scheduled_date)

        # For new objects, ensure the date is timezone-aware and avoid duplicates
        if not self.pk:
            if self.scheduled_date and timezone.is_naive(self.scheduled_date):
                self.scheduled_date = timezone.make_aware(self.scheduled_date)
            if MaintenanceSchedule.objects.filter(
                elevator=self.elevator, 
                scheduled_date=self.scheduled_date
            ).exists():
                raise IntegrityError(
                    f"A maintenance schedule for elevator {self.elevator.id} already exists on {self.scheduled_date}"
                )
            super().save(*args, **kwargs)
            return

        # For existing objects, update status if the scheduled_date is in the past
        if self.status not in ['overdue', 'completed']:
            if timezone.is_naive(self.scheduled_date):
                self.scheduled_date = timezone.make_aware(self.scheduled_date)
            if self.status == 'scheduled' and self.scheduled_date < timezone.now():
                self.status = 'overdue'
                logger.info(f"Schedule {self.id} marked as overdue")
                
        super().save(*args, **kwargs)

    def get_next_scheduled_date(self):
        """Calculate the next scheduled date based on next_schedule setting."""
        if self.next_schedule == '1_month':
            return self.scheduled_date + relativedelta(months=1)
        elif self.next_schedule == '3_months':
            return self.scheduled_date + relativedelta(months=3)
        elif self.next_schedule == '6_months':
            return self.scheduled_date + relativedelta(months=6)
        return None

    def create_next_schedule(self):
        """Create the next schedule if it doesn't already exist."""
        next_date = self.get_next_scheduled_date()
        if not next_date:
            return None

        # Adjust if the date falls on a weekend
        while next_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            next_date += timezone.timedelta(days=1)

        # Check if a schedule already exists for this elevator on next_date
        existing_schedule = MaintenanceSchedule.objects.filter(
            elevator=self.elevator,
            scheduled_date=next_date
        ).first()

        if existing_schedule:
            logger.info(f"Schedule already exists for elevator {self.elevator.id} on {next_date}")
            return existing_schedule

        new_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date=next_date,
            next_schedule=self.next_schedule,
            description=self.description,
            status='scheduled'
        )
        logger.info(f"Created new schedule {new_schedule.id} for elevator {self.elevator.id}")
        return new_schedule

# Pre-save signal (optional if you want to catch overdue status earlier)
@receiver(pre_save, sender=MaintenanceSchedule)
def update_schedule_status(sender, instance, **kwargs):
    """Signal handler to update schedule status before save."""
    if instance.status == 'scheduled' and instance.scheduled_date < timezone.now():
        instance.status = 'overdue'
        logger.info(f"Pre-save signal: Schedule {instance.id} marked as overdue")

# Post-save signal to trigger new schedule creation
@receiver(post_save, sender=MaintenanceSchedule)
def create_schedule_on_status_change(sender, instance, created, **kwargs):
    """
    Automatically create a new schedule after a maintenance schedule is updated 
    and its status is either 'overdue' or 'completed'.
    """
    # Only act on updates (not on initial creation)
    if not created and instance.status in ['overdue', 'completed']:
        instance.create_next_schedule()


class ElevatorConditionReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.CASCADE, related_name="condition_reports")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="condition_reports")
    date_inspected = models.DateTimeField(default=timezone.now)
    

    # Assessment fields
    alarm_bell = models.CharField(max_length=255, blank=True, null=True)
    noise_during_motion = models.CharField(max_length=255, blank=True, null=True)
    cabin_lights = models.CharField(max_length=255, blank=True, null=True)
    position_indicators = models.CharField(max_length=255, blank=True, null=True)
    hall_lantern_indicators = models.CharField(max_length=255, blank=True, null=True)
    cabin_flooring = models.CharField(max_length=255, blank=True, null=True)
    additional_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Condition Report for Schedule ID: {self.maintenance_schedule.id} | Inspected: {self.date_inspected}"

    class Meta:
        verbose_name = "Elevator Condition Report"
        verbose_name_plural = "Elevator Condition Reports"


class ScheduledMaintenanceLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.CASCADE, related_name="maintenance_logs")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="maintenance_logs")
    condition_report = models.OneToOneField(ElevatorConditionReport, on_delete=models.CASCADE, related_name="maintenance_log")
    date_completed = models.DateTimeField(default=now)

    # Checklist fields
    check_machine_gear = models.BooleanField(default=False)
    check_machine_brake = models.BooleanField(default=False)
    check_controller_connections = models.BooleanField(default=False)
    blow_dust_from_controller = models.BooleanField(default=False)
    clean_machine_room = models.BooleanField(default=False)
    clean_guide_rails = models.BooleanField(default=False)
    observe_operation = models.BooleanField(default=False)

    # Description and observations
    description = models.TextField(blank=True, null=True)

    # Oversight and approval
    overseen_by = models.CharField(max_length=255, blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Log for Schedule ID: {self.maintenance_schedule.id} | Completed: {self.date_completed}"

    class Meta:
        verbose_name = "Scheduled Maintenance Log"
        verbose_name_plural = "Scheduled Maintenance Logs"


class AdHocMaintenanceSchedule(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('overdue', 'Overdue'),
        ('completed', 'Completed')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    elevator = models.ForeignKey(Elevator, on_delete=models.CASCADE, related_name="ad_hoc_schedules")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="ad_hoc_schedules")
    maintenance_company = models.ForeignKey(MaintenanceCompanyProfile, on_delete=models.CASCADE, related_name="ad_hoc_schedules")
    scheduled_date = models.DateTimeField(default=now)
    description = models.TextField(help_text="Briefly describe the purpose of this ad-hoc schedule.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    def __str__(self):
        return f"Ad-Hoc Schedule | Elevator: {self.elevator.user_name} | Date: {self.scheduled_date} | Status: {self.status}"

    class Meta:
        verbose_name = "Ad-Hoc Maintenance Schedule"
        verbose_name_plural = "Ad-Hoc Maintenance Schedules"


class AdHocElevatorConditionReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ad_hoc_schedule = models.ForeignKey(AdHocMaintenanceSchedule, on_delete=models.CASCADE, related_name="condition_reports")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="ad_hoc_condition_reports")
    date_inspected = models.DateTimeField(default=now)

    # Updated fields for dynamic reporting
    components_checked = models.CharField(max_length=255, help_text="List of components or parts of the elevator inspected during this visit.")
    condition = models.TextField(help_text="Condition of the components checked.")

    def __str__(self):
        return f"Ad-Hoc Condition Report | Schedule ID: {self.ad_hoc_schedule.id} | Inspected: {self.date_inspected}"

    class Meta:
        verbose_name = "Ad-Hoc Elevator Condition Report"
        verbose_name_plural = "Ad-Hoc Elevator Condition Reports"


class AdHocMaintenanceLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ad_hoc_schedule = models.ForeignKey(AdHocMaintenanceSchedule, on_delete=models.CASCADE, related_name="maintenance_logs")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="ad_hoc_maintenance_logs")
    condition_report = models.OneToOneField(AdHocElevatorConditionReport, on_delete=models.CASCADE, related_name="ad_hoc_maintenance_log")
    date_completed = models.DateTimeField(default=now)

    # Updated field for task summary
    summary_title = models.CharField(max_length=255, help_text="Brief summary of the work done during this maintenance.")
    description = models.TextField(blank=True, null=True)

    # Oversight and approval
    overseen_by = models.CharField(max_length=255, blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Ad-Hoc Maintenance Log | Schedule ID: {self.ad_hoc_schedule.id} | Completed: {self.date_completed}"

    class Meta:
        verbose_name = "Ad-Hoc Maintenance Log"
        verbose_name_plural = "Ad-Hoc Maintenance Logs"


class BuildingLevelAdhocSchedule(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('overdue', 'Overdue'),
        ('completed', 'Completed')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name="building_level_adhoc_schedules")
    technician = models.ForeignKey(TechnicianProfile, on_delete=models.CASCADE, related_name="building_level_adhoc_schedules")
    maintenance_company = models.ForeignKey(MaintenanceCompanyProfile, on_delete=models.CASCADE, related_name="building_level_adhoc_schedules")
    scheduled_date = models.DateTimeField(default=now)
    description = models.TextField(help_text="Briefly describe the purpose of this ad-hoc schedule.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = "Building Level Adhoc Schedule"
        verbose_name_plural = "Building Level Adhoc Schedules"

    def __str__(self):
        return f"Adhoc Schedule for Building {self.building.name} (Status: {self.get_status_display()})"


class MaintenanceCheck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    maintenance_schedule = models.ForeignKey(MaintenanceSchedule, on_delete=models.CASCADE, related_name='checks')
    task_description = models.CharField(max_length=255)
    passed = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Check for Schedule ID: {self.maintenance_schedule.id} | Task: {self.task_description}"


class AdHocMaintenanceTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField()
    created_by = models.ForeignKey(MaintenanceCompanyProfile, on_delete=models.CASCADE, related_name="adhoc_tasks")
    assigned_to = models.ForeignKey(TechnicianProfile, on_delete=models.SET_NULL, null=True, related_name="adhoc_tasks")
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateTimeField()
    completed = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Ad-Hoc Task | Created By: {self.created_by.company_name} | Assigned To: {self.assigned_to.user.first_name if self.assigned_to else 'Unassigned'}"
