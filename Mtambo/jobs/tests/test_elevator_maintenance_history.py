from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from uuid import uuid4
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule
from jobs.factories import (
    ElevatorFactory, MaintenanceScheduleFactory, AdHocMaintenanceScheduleFactory
)


class ElevatorMaintenanceHistoryViewTest(APITestCase):
    def setUp(self):
        self.elevator = ElevatorFactory()
        self.completed_regular_schedule = MaintenanceScheduleFactory(
            elevator=self.elevator, status='completed'
        )
        self.completed_adhoc_schedule = AdHocMaintenanceScheduleFactory(
            elevator=self.elevator, status='completed'
        )
        self.url = reverse('elevator-maintenance-history', kwargs={'elevator_id': self.elevator.id})

    def test_get_elevator_maintenance_history_success(self):
        """Ensure we can retrieve completed maintenance schedules for a specific elevator."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 2)

    def test_get_elevator_maintenance_history_invalid_elevator(self):
        """Ensure requesting history for a non-existent elevator returns a 200 but empty list."""
        invalid_url = reverse('elevator-maintenance-history', kwargs={'elevator_id': uuid4()})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

