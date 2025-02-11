import json
from uuid import uuid4
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from jobs.factories import (
    MaintenanceScheduleFactory,
    AdHocMaintenanceScheduleFactory,
    TechnicianProfileFactory,
    MaintenanceCompanyProfileFactory,
)
from jobs.models import (
    MaintenanceSchedule,
    AdHocMaintenanceSchedule,
    ElevatorConditionReport,
    AdHocElevatorConditionReport,
    ScheduledMaintenanceLog,
    AdHocMaintenanceLog,
)

class FileMaintenanceLogViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.technician = TechnicianProfileFactory()
        self.maintenance_company = MaintenanceCompanyProfileFactory()
        self.regular_schedule = MaintenanceScheduleFactory(
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            status='scheduled',
            scheduled_date=timezone.now() + timezone.timedelta(days=1)  # Ensure a future date for testing
        )
        self.adhoc_schedule = AdHocMaintenanceScheduleFactory(
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            status='scheduled',
            scheduled_date=timezone.now() + timezone.timedelta(days=1)  # Ensure a future date for testing
        )
        self.valid_regular_data = {
            'schedule_type': 'regular',
            'condition_report': {
                'maintenance_schedule': str(self.regular_schedule.id),
                'technician': str(self.technician.id),
                'components_checked': 'Checked components',
                'condition': 'Good condition',
            },
            'maintenance_log': {
                'performed_tasks': [
                    {'task_name': 'Test Task', 'status': 'completed'}
                ],
                'check_machine_gear': True,
                'check_machine_brake': True,
                'check_controller_connections': True,
                'blow_dust_from_controller': True,
                'clean_machine_room': True,
                'clean_guide_rails': True,
                'observe_operation': True,
                'description': 'Regular maintenance completed',
            }
        }
        self.valid_adhoc_data = {
            'schedule_type': 'adhoc',
            'condition_report': {
                'maintenance_schedule': str(self.adhoc_schedule.id),
                'technician': str(self.technician.id),
                'components_checked': 'Checked components',
                'condition': 'Good condition',
            },
            'maintenance_log': {
                'summary_title': 'Ad-hoc Maintenance Summary',
                'description': 'Ad-hoc maintenance completed',
            }
        }

    # Helper method to get URL
    def get_url(self, schedule_id):
        return reverse('file-maintenance-log', kwargs={'schedule_id': schedule_id})

    # Test Cases

    def test_invalid_uuid(self):
        invalid_uuid = str(uuid4())  # Generate a valid UUID
        response = self.client.post(
            self.get_url(invalid_uuid),
            data=self.valid_regular_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_schedule_type(self):
        invalid_data = self.valid_regular_data.copy()
        invalid_data['schedule_type'] = 'invalid'
        response = self.client.post(
            self.get_url(self.regular_schedule.id),
            data=invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid schedule type. Must be either 'regular' or 'adhoc'.")

    def test_schedule_not_found(self):
        non_existent_uuid = uuid4()
        response = self.client.post(
            self.get_url(non_existent_uuid),
            data=self.valid_regular_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_regular_maintenance_success(self):
        response = self.client.post(
            self.get_url(self.regular_schedule.id),
            data=self.valid_regular_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.regular_schedule.refresh_from_db()
        self.assertEqual(self.regular_schedule.status, 'completed')
        self.assertEqual(ElevatorConditionReport.objects.count(), 1)
        self.assertEqual(ScheduledMaintenanceLog.objects.count(), 1)

    def test_adhoc_maintenance_success(self):
        response = self.client.post(
            self.get_url(self.adhoc_schedule.id),
            data=self.valid_adhoc_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.adhoc_schedule.refresh_from_db()
        self.assertEqual(self.adhoc_schedule.status, 'completed')
        self.assertEqual(AdHocElevatorConditionReport.objects.count(), 1)
        self.assertEqual(AdHocMaintenanceLog.objects.count(), 1)

    def test_missing_condition_report(self):
        invalid_data = self.valid_regular_data.copy()
        del invalid_data['condition_report']
        response = self.client.post(
            self.get_url(self.regular_schedule.id),
            data=invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Condition report required.")

    def test_missing_maintenance_log(self):
        invalid_data = self.valid_regular_data.copy()
        del invalid_data['maintenance_log']
        response = self.client.post(
            self.get_url(self.regular_schedule.id),
            data=invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Maintenance log data required.")

    def test_regular_missing_required_fields(self):
        invalid_data = self.valid_regular_data.copy()
        del invalid_data['maintenance_log']['check_machine_gear']
        response = self.client.post(
            self.get_url(self.regular_schedule.id),
            data=invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("check_machine_gear", response.data['detail'])

    def test_adhoc_missing_summary_title(self):
        invalid_data = self.valid_adhoc_data.copy()
        del invalid_data['maintenance_log']['summary_title']
        response = self.client.post(
            self.get_url(self.adhoc_schedule.id),
            data=invalid_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Summary title required for ad-hoc maintenance.")

    def test_schedule_already_completed(self):
        completed_schedule = MaintenanceScheduleFactory(status='completed')
        response = self.client.post(
            self.get_url(completed_schedule.id),
            data=self.valid_regular_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Schedule already completed.")

    def test_no_technician_assigned(self):
        schedule = MaintenanceScheduleFactory(technician=None, status='scheduled')
        response = self.client.post(
            self.get_url(schedule.id),
            data=self.valid_regular_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "No technician assigned.")

    def test_no_maintenance_company_assigned(self):
        schedule = MaintenanceScheduleFactory(maintenance_company=None, status='scheduled')
        response = self.client.post(
            self.get_url(schedule.id),
            data=self.valid_regular_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "No maintenance company assigned.")

    def test_schedule_status_update_to_overdue(self):
        overdue_schedule = MaintenanceScheduleFactory(
            status='scheduled', 
            scheduled_date=timezone.now() - timezone.timedelta(days=1)
        )
        response = self.client.post(
            self.get_url(overdue_schedule.id),
            data=self.valid_regular_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        overdue_schedule.refresh_from_db()
        self.assertEqual(overdue_schedule.status, 'overdue')

