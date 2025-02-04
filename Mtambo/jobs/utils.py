from datetime import timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_next_scheduled_date(scheduled_date, months_to_add):
    """
    Given a scheduled date and the number of months to add, returns the new scheduled date.
    If no scheduled date is provided or months_to_add is 0 or negative, the function returns the original scheduled date.
    The function ensures that the scheduled date does not fall on a weekend (Saturday or Sunday).
    """
    if scheduled_date is None:
        logger.warning("Scheduled date is None, returning None.")
        return None

    if months_to_add > 0:
        next_date = scheduled_date + relativedelta(months=+months_to_add)
        
        # Adjust if the calculated date falls on a weekend
        if next_date.weekday() == 5:  # Saturday
            next_date += timedelta(days=2)  # Move to Monday
        elif next_date.weekday() == 6:  # Sunday
            next_date += timedelta(days=1)  # Move to Monday

        return next_date
    else:
        logger.warning(f"Invalid months_to_add value ({months_to_add}). Returning original scheduled date.")
        return scheduled_date

def create_new_maintenance_schedule(maintenance_schedule):
    """
    Creates a new maintenance schedule based on the current schedule's configuration.
    Ensures that the next scheduled date does not fall on a weekend (Saturday or Sunday).
    """
    from .models import MaintenanceSchedule  # Lazy import inside the function

    technician = maintenance_schedule.elevator.technician if maintenance_schedule.elevator.technician else None
    maintenance_company = maintenance_schedule.elevator.maintenance_company if maintenance_schedule.elevator.maintenance_company else None

    # Calculate the next scheduled date based on the current schedule's 'next_schedule' choice
    next_scheduled_date = None  # Variable to hold the date of the next schedule

    if maintenance_schedule.next_schedule == '1_month':
        next_scheduled_date = maintenance_schedule.scheduled_date + timezone.timedelta(days=30)
    elif maintenance_schedule.next_schedule == '3_months':
        next_scheduled_date = maintenance_schedule.scheduled_date + timezone.timedelta(days=90)
    elif maintenance_schedule.next_schedule == '6_months':
        next_scheduled_date = maintenance_schedule.scheduled_date + timezone.timedelta(days=180)
    elif maintenance_schedule.next_schedule == 'set_date' and maintenance_schedule.scheduled_date:
        next_scheduled_date = maintenance_schedule.scheduled_date  # Adjust this as needed for specific set dates

    # If the next scheduled date is determined, proceed with creating a new schedule
    if next_scheduled_date:
        # Ensure the new schedule doesn't fall on a weekend
        if next_scheduled_date.weekday() == 5:  # Saturday
            next_scheduled_date += timedelta(days=2)  # Move to Monday
        elif next_scheduled_date.weekday() == 6:  # Sunday
            next_scheduled_date += timedelta(days=1)  # Move to Monday

        # Create the new maintenance schedule
        new_schedule = MaintenanceSchedule(
            elevator=maintenance_schedule.elevator,
            technician=technician,
            maintenance_company=maintenance_company,
            scheduled_date=next_scheduled_date,
            next_schedule=maintenance_schedule.next_schedule,
            description=maintenance_schedule.description,
            status='scheduled',  # Ensure the new schedule has a status of 'scheduled'
        )
        new_schedule.save()
        logger.info(f"New schedule created with ID {new_schedule.id} for elevator {maintenance_schedule.elevator.id}")
    else:
        logger.warning(f"Could not create a new schedule for elevator {maintenance_schedule.elevator.id}, next_scheduled_date is None.")

def update_schedule_status_and_create_new_schedule(maintenance_schedule):
    """
    Updates the status of the current maintenance schedule to 'overdue' or 'completed',
    and creates a new schedule if needed. Ensures the next scheduled date doesn't fall on a weekend.
    """
    # Check if the schedule is already completed or overdue
    if maintenance_schedule.status in ['completed', 'overdue']:
        #logger.info(f"Skipping schedule creation for schedule {maintenance_schedule.id} as it's already completed or overdue.")
        #return

        # Update status logic based on time
        if maintenance_schedule.status == 'scheduled' and maintenance_schedule.scheduled_date < timezone.now():
            maintenance_schedule.status = 'overdue'
            maintenance_schedule.save()
            logger.info(f"Schedule {maintenance_schedule.id} is overdue.")

        # Create a new schedule based on the current schedule
        create_new_maintenance_schedule(maintenance_schedule)
