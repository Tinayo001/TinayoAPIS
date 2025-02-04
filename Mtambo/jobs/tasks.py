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
    try:
        from jobs.utils import update_schedule_status_and_create_new_schedule

        # Get the current time
        now = timezone.now()

        # Query all normal maintenance schedules that are still 'scheduled'
        overdue_normal_schedules = MaintenanceSchedule.objects.filter(status='scheduled')
        overdue_adhoc_schedules = AdHocMaintenanceSchedule.objects.filter(status='scheduled')
        overdue_building_adhoc_schedules = BuildingLevelAdhocSchedule.objects.filter(status='scheduled')

        overdue_normal_count = 0
        overdue_adhoc_count = 0
        overdue_building_adhoc_count = 0
        processed_schedules = {
            'normal': [],
            'adhoc': [],
            'building_adhoc': []
        }

        # Process normal maintenance schedules
        for schedule in overdue_normal_schedules:
            scheduled_date_end_of_day = timezone.make_aware(
                timezone.datetime.combine(schedule.scheduled_date.date(), timezone.datetime.min.time()) + timedelta(days=1) - timedelta(microseconds=1)
            )

            if scheduled_date_end_of_day < now:
                overdue_normal_count += 1
                try:
                    if schedule.status not in ['completed', 'overdue']:
                        schedule.status = 'overdue'
                        schedule.save()
                        logger.info(f"Updated normal schedule {schedule.id} status to 'overdue'.")
                        processed_schedules['normal'].append(schedule.id)

                        # Create a new maintenance schedule for the next period
                        update_schedule_status_and_create_new_schedule(schedule)
                        logger.info(f"New maintenance schedule created for normal schedule {schedule.id}.")

                except Exception as e:
                    logger.error(f"Error processing normal schedule {schedule.id}: {str(e)}")
                    return {
                        'status': 'error',
                        'error': f"Error processing normal schedule {schedule.id}: {str(e)}",
                        'timestamp': str(now)
                    }

        # Process ad-hoc maintenance schedules
        for schedule in overdue_adhoc_schedules:
            scheduled_date_end_of_day = timezone.make_aware(
                timezone.datetime.combine(schedule.scheduled_date.date(), timezone.datetime.min.time()) + timedelta(days=1) - timedelta(microseconds=1)
            )

            if scheduled_date_end_of_day < now:
                overdue_adhoc_count += 1
                try:
                    if schedule.status not in ['completed', 'overdue']:
                        schedule.status = 'overdue'
                        schedule.save()
                        logger.info(f"Updated ad-hoc schedule {schedule.id} status to 'overdue'.")
                        processed_schedules['adhoc'].append(schedule.id)

                except Exception as e:
                    logger.error(f"Error processing ad-hoc schedule {schedule.id}: {str(e)}")
                    return {
                        'status': 'error',
                        'error': f"Error processing ad-hoc schedule {schedule.id}: {str(e)}",
                        'timestamp': str(now)
                    }

        # Process building-level ad-hoc maintenance schedules
        for schedule in overdue_building_adhoc_schedules:
            scheduled_date_end_of_day = timezone.make_aware(
                timezone.datetime.combine(schedule.scheduled_date.date(), timezone.datetime.min.time()) + timedelta(days=1) - timedelta(microseconds=1)
            )

            if scheduled_date_end_of_day < now:
                overdue_building_adhoc_count += 1
                try:
                    if schedule.status not in ['completed', 'overdue']:
                        schedule.status = 'overdue'
                        schedule.save()
                        logger.info(f"Updated building-level ad-hoc schedule {schedule.id} status to 'overdue'.")
                        processed_schedules['building_adhoc'].append(schedule.id)

                except Exception as e:
                    logger.error(f"Error processing building-level ad-hoc schedule {schedule.id}: {str(e)}")
                    return {
                        'status': 'error',
                        'error': f"Error processing building-level ad-hoc schedule {schedule.id}: {str(e)}",
                        'timestamp': str(now)
                    }

        logger.info(f"Processed {overdue_normal_count} overdue normal schedules.")
        logger.info(f"Processed {overdue_adhoc_count} overdue ad-hoc schedules.")
        logger.info(f"Processed {overdue_building_adhoc_count} overdue building-level ad-hoc schedules.")

        # Return summary of processing
        return {
            'status': 'success',
            'timestamp': str(now),
            'processed_counts': {
                'normal_schedules': overdue_normal_count,
                'adhoc_schedules': overdue_adhoc_count,
                'building_adhoc_schedules': overdue_building_adhoc_count
            },
            'processed_ids': processed_schedules
        }

    except Exception as e:
        logger.error(f"Unexpected error in check_overdue_schedules: {str(e)}")
        return {
            'status': 'error',
            'error': f"Unexpected error: {str(e)}",
            'timestamp': str(now)
        }
