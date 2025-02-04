from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from jobs.models import AdHocMaintenanceSchedule
from jobs.factories import ElevatorFactory, UserFactory

class CreateAdHocMaintenanceScheduleViewTest(APITestCase):
    
    def setUp(self):
        self.user = UserFactory.create()
        self.elevator = ElevatorFactory.create()
        self.client.force_authenticate(user=self.user)
        self.url = reverse("create_ad_hoc_maintenance_schedule", kwargs={"elevator_uuid": str(self.elevator.id)})
    
    def test_create_adhoc_schedule_success(self):
        scheduled_date = (timezone.now() + timedelta(days=1)).isoformat()
        data = {
            "scheduled_date": scheduled_date,
            "description": "Routine elevator maintenance"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("message", response.data)
        self.assertEqual(response.data["message"], "Ad-Hoc maintenance schedule created successfully")
        self.assertIn("maintenance_schedule_id", response.data)
        self.assertTrue(AdHocMaintenanceSchedule.objects.filter(id=response.data["maintenance_schedule_id"]).exists())
    
    def test_create_adhoc_schedule_missing_description(self):
        scheduled_date = (timezone.now() + timedelta(days=1)).isoformat()
        data = {
            "scheduled_date": scheduled_date,
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Missing required field: description.")
    
    def test_create_adhoc_schedule_missing_scheduled_date(self):
        data = {
            "description": "Routine elevator maintenance"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Missing required field: scheduled_date.")
    
    def test_create_adhoc_schedule_invalid_date_format(self):
        # Generate a future date-only string (e.g., tomorrow)
        future_date = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        data = {
            "scheduled_date": future_date,  # Date-only string
            "description": "Routine elevator maintenance"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("maintenance_schedule_id", response.data)
        maintenance_schedule = AdHocMaintenanceSchedule.objects.get(id=response.data["maintenance_schedule_id"])
        self.assertEqual(maintenance_schedule.scheduled_date.strftime("%H:%M:%S"), "00:00:00")
    
    def test_create_adhoc_schedule_past_date(self):
        data = {
            "scheduled_date": (timezone.now() - timedelta(days=1)).isoformat(),
            "description": "Routine elevator maintenance"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "The scheduled date cannot be in the past. Please choose a future date.")

    def test_create_adhoc_schedule_unauthenticated(self):
        # Remove forced authentication:
        self.client.force_authenticate(user=None)
    
        scheduled_date = (timezone.now() + timedelta(days=1)).isoformat()
        data = {
            "scheduled_date": scheduled_date,
            "description": "Routine elevator maintenance"
        }
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
         
