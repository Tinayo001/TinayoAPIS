from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from developers.models import DeveloperProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import (
    MaintenanceSchedule,
    ScheduledMaintenanceLog,
    AdHocMaintenanceSchedule,
    AdHocMaintenanceLog,
)
from jobs.factories import (
    DeveloperProfileFactory,
    BuildingFactory,
    ElevatorFactory,
    MaintenanceScheduleFactory,
    ScheduledMaintenanceLogFactory,
    AdHocMaintenanceScheduleFactory,
    AdHocMaintenanceLogFactory,
)


class DeveloperMaintenanceLogApprovalViewTest(APITestCase):
    def setUp(self):
        self.developer = DeveloperProfileFactory.create()
        self.building = BuildingFactory.create(developer=self.developer)
        self.elevator = ElevatorFactory.create(building=self.building, developer=self.developer)

        # Create a regular maintenance schedule and log.
        self.maintenance_schedule = MaintenanceScheduleFactory.create(
            elevator=self.elevator,
            status="completed"
        )
        self.scheduled_log = ScheduledMaintenanceLogFactory.create(
            maintenance_schedule=self.maintenance_schedule,
            approved_by=None
        )

        # Create an adhoc maintenance schedule and log.
        self.adhoc_schedule = AdHocMaintenanceScheduleFactory.create(
            elevator=self.elevator,
            status="completed"
        )
        self.adhoc_log = AdHocMaintenanceLogFactory.create(
            ad_hoc_schedule=self.adhoc_schedule,
            approved_by=None
        )

        self.url = reverse('developer-maintenance-log-approval', kwargs={'developer_uuid': self.developer.id})
        self.client.credentials(HTTP_ACCEPT='application/json')

    def test_get_unapproved_logs(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('unapproved_regular_schedules', data)
        self.assertIn('unapproved_adhoc_schedules', data)
        self.assertGreaterEqual(len(data['unapproved_adhoc_schedules']), 1)
        adhoc_schedule_data = data['unapproved_adhoc_schedules'][0]['maintenance_schedule']
        self.assertEqual(adhoc_schedule_data['id'], str(self.adhoc_schedule.id))

    def test_put_approve_logs_success(self):
        payload = {
            "regular_maintenance_log_uuids": [str(self.scheduled_log.id)],
            "adhoc_maintenance_log_uuids": [str(self.adhoc_log.id)]
        }
        response = self.client.put(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('successful_approvals', data)
        self.assertEqual(len(data['successful_approvals']), 2)
        self.assertEqual(data['not_found'], [])
        self.assertEqual(data['already_approved'], [])
        self.scheduled_log.refresh_from_db()
        self.adhoc_log.refresh_from_db()
        self.assertIsNotNone(self.scheduled_log.approved_by)
        self.assertIsNotNone(self.adhoc_log.approved_by)

    def test_put_logs_not_belonging_to_developer(self):
        other_developer = DeveloperProfileFactory.create()
        other_building = BuildingFactory.create(developer=other_developer)
        other_elevator = ElevatorFactory.create(building=other_building, developer=other_developer)
        other_schedule = MaintenanceScheduleFactory.create(elevator=other_elevator, status="completed")
        other_log = ScheduledMaintenanceLogFactory.create(maintenance_schedule=other_schedule, approved_by=None)
        payload = {
            "regular_maintenance_log_uuids": [str(other_log.id)],
            "adhoc_maintenance_log_uuids": []
        }
        response = self.client.put(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        data = response.json()
        self.assertIn("does not belong", data.get("detail", ""))

    def test_put_logs_not_found(self):
        non_existent_uuid = "00000000-0000-0000-0000-000000000000"
        payload = {
            "regular_maintenance_log_uuids": [non_existent_uuid],
            "adhoc_maintenance_log_uuids": []
        }
        response = self.client.put(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        # The view returns the "not_found" information under the "data" key.
        self.assertIn('data', data)
        self.assertIn('not_found', data['data'])
        self.assertEqual(len(data['data']['not_found']), 1)

    def test_get_no_unapproved_logs(self):
        self.scheduled_log.approved_by = "AlreadyApproved"
        self.scheduled_log.save()
        self.adhoc_log.approved_by = "AlreadyApproved"
        self.adhoc_log.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertEqual(data['detail'], "No pending unapproved maintenance logs for this developer.")

