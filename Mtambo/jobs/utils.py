from django.utils import timezone
from dateutil.relativedelta import relativedelta
import logging

logger = logging.getLogger(__name__)

def get_next_scheduled_date(current_date, next_schedule_type):
    """
    Calculate the next scheduled date and handle weekend adjustments.
    """
    if next_schedule_type == '1_month':
        next_date = current_date + relativedelta(months=1)
    elif next_schedule_type == '3_months':
        next_date = current_date + relativedelta(months=3)
    elif next_schedule_type == '6_months':
        next_date = current_date + relativedelta(months=6)
    else:
        return None
    # Adjust if the date falls on a weekend
    while next_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        next_date += timezone.timedelta(days=1)
    return next_date
def create_new_maintenance_schedule(maintenance_schedule):
    """
    Creates a new maintenance schedule if one doesn't already exist.
    """
    next_date = get_next_scheduled_date(
        maintenance_schedule.scheduled_date,
        maintenance_schedule.next_schedule
    )

    if not next_date:
        logger.info(f"No next date calculated for schedule {maintenance_schedule.id}")
        return None
    # Use get_or_create to prevent duplicates
    from .models import MaintenanceSchedule
    new_schedule, created = MaintenanceSchedule.objects.get_or_create(
        elevator=maintenance_schedule.elevator,
        scheduled_date=next_date,
        defaults={
            'technician': maintenance_schedule.technician,
            'maintenance_company': maintenance_schedule.maintenance_company,
            'next_schedule': maintenance_schedule.next_schedule,
            'description': maintenance_schedule.description,
            'status': 'scheduled'
        }
    )
    if created:
        logger.info(f"Created new schedule {new_schedule.id} for elevator {maintenance_schedule.elevator.id}")
    else:
        logger.info(f"Schedule already exists for elevator {maintenance_schedule.elevator.id} on {next_date}")
    return new_schedule
def update_schedule_status_and_create_new_schedule(maintenance_schedule):
    """
    Updates the status of the current maintenance schedule and creates a new schedule if needed.
    """
    now = timezone.now()

    try:
        if maintenance_schedule.status == 'scheduled' and maintenance_schedule.scheduled_date < now:
            # Mark as overdue
            maintenance_schedule.status = 'overdue'
            maintenance_schedule.save()
            logger.info(f"Schedule {maintenance_schedule.id} marked as overdue")

            # Create new schedule if needed
            new_schedule = create_new_maintenance_schedule(maintenance_schedule)
            if new_schedule:
                logger.info(f"Created new schedule {new_schedule.id} following overdue schedule")

        elif maintenance_schedule.status == 'completed':
            # Only create new schedule if it's completed and doesn't already exist
            new_schedule = create_new_maintenance_schedule(maintenance_schedule)
            if new_schedule:
                logger.info(f"Created new schedule {new_schedule.id} following completed schedule")

        else:
            logger.info(f"No status update needed for schedule {maintenance_schedule.id}")

    except Exception as e:
        logger.error(f"Error processing schedule {maintenance_schedule.id}: {str(e)}")
        raise
def is_weekend(date):
    """
    Check if a given date falls on a weekend.
    """
    return date.weekday() >= 5  # 5 = Saturday, 6 = Sunday
def get_next_business_day(date):
    """
    Get the next business day after a given date.
    """
    next_day = date + timezone.timedelta(days=1)
    while is_weekend(next_day):
        next_day += timezone.timedelta(days=1)
    return next_day
