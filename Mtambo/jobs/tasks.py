from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
import logging

# Set up logging
logger = logging.getLogger(__name__)

@shared_task
def check_overdue_schedules():
    """
    Check if any maintenance schedules (normal, ad-hoc, or building-level ad-hoc) are overdue and update their status
    to 'overdue' if necessary. Normal schedules will trigger the creation of new schedules,
    while ad-hoc schedules will not.
    """
    from jobs.utils import update_schedule_status_and_create_new_schedule

    # Get the current time
    now = timezone.now()

    # Log the current time for debugging
    logger.info(f"Current time: {now}")

    # Query all normal maintenance schedules that are still 'scheduled'
    overdue_normal_schedules = MaintenanceSchedule.objects.filter(status='scheduled')
    logger.info(f"Found {overdue_normal_schedules.count()} normal scheduled maintenance schedules.")

    # Query all ad-hoc maintenance schedules that are still 'scheduled'
    overdue_adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(status='scheduled')
    logger.info(f"Found {overdue_adhoc_schedules.count()} ad-hoc scheduled maintenance schedules.")

    # Query all building-level ad-hoc maintenance schedules that are still 'scheduled'
    overdue_building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.filter(status='scheduled')
    logger.info(f"Found {overdue_building_adhoc_schedules.count()} building-level ad-hoc scheduled maintenance schedules.")

    # Process normal maintenance schedules
    for schedule in overdue_normal_schedules:
        # Adjust the scheduled_date to the end of the day (23:59:59)
        scheduled_date_end_of_day = timezone.make_aware(
            timezone.datetime.combine(schedule.scheduled_date.date(), timezone.datetime.min.time()) + timedelta(days=1) - timedelta(microseconds=1)
        )
        
        logger.info(f"Normal schedule {schedule.id} scheduled date (end of day): {scheduled_date_end_of_day}")

        if scheduled_date_end_of_day < now:
            try:
                if schedule.status not in ['completed', 'overdue']:
                    schedule.status = 'overdue'
                    schedule.save()
                    logger.info(f"Updated normal schedule {schedule.id} status to 'overdue'.")

                    # Create a new maintenance schedule for the next period
                    update_schedule_status_and_create_new_schedule(schedule)
                    logger.info(f"New maintenance schedule created for normal schedule {schedule.id}.")

            except Exception as e:
                logger.error(f"Error processing normal schedule {schedule.id}: {str(e)}")

    # Process ad-hoc maintenance schedules
    for schedule in overdue_adhoc_schedules:
        # Adjust the scheduled_date to the end of the day (23:59:59)
        scheduled_date_end_of_day = timezone.make_aware(
            timezone.datetime.combine(schedule.scheduled_date.date(), timezone.datetime.min.time()) + timedelta(days=1) - timedelta(microseconds=1)
        )

        logger.info(f"Ad-hoc schedule {schedule.id} scheduled date (end of day): {scheduled_date_end_of_day}")

        if scheduled_date_end_of_day < now:
            try:
                if schedule.status not in ['completed', 'overdue']:
                    schedule.status = 'overdue'
                    schedule.save()
                    logger.info(f"Updated ad-hoc schedule {schedule.id} status to 'overdue'.")

            except Exception as e:
                logger.error(f"Error processing ad-hoc schedule {schedule.id}: {str(e)}")

    # Process building-level ad-hoc maintenance schedules
    for schedule in overdue_building_adhoc_schedules:
        # Adjust the scheduled_date to the end of the day (23:59:59)
        scheduled_date_end_of_day = timezone.make_aware(
            timezone.datetime.combine(schedule.scheduled_date.date(), timezone.datetime.min.time()) + timedelta(days=1) - timedelta(microseconds=1)
        )

        logger.info(f"Building-level ad-hoc schedule {schedule.id} scheduled date (end of day): {scheduled_date_end_of_day}")

        if scheduled_date_end_of_day < now:
            try:
                if schedule.status not in ['completed', 'overdue']:
                    schedule.status = 'overdue'
                    schedule.save()
                    logger.info(f"Updated building-level ad-hoc schedule {schedule.id} status to 'overdue'.")

            except Exception as e:
                logger.error(f"Error processing building-level ad-hoc schedule {schedule.id}: {str(e)}")

    logger.info(f"Processed {overdue_normal_schedules.count()} overdue normal schedules.")
    logger.info(f"Processed {overdue_adhoc_schedules.count()} overdue ad-hoc schedules.")
    logger.info(f"Processed {overdue_building_adhoc_schedules.count()} overdue building-level ad-hoc schedules.")

