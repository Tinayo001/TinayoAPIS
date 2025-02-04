from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from technicians.models import TechnicianProfile
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from jobs.factories import TechnicianProfileFactory, MaintenanceScheduleFactory, AdHocMaintenanceScheduleFactory, BuildingLevelAdhocScheduleFactory

class TechnicianJobStatusViewTest(APITestCase):
    def setUp(self):
        self.technician = TechnicianProfileFactory()
        
        # Creating scheduled jobs
        self.scheduled_regular = MaintenanceScheduleFactory(technician=self.technician, status="scheduled")
        self.scheduled_adhoc = AdHocMaintenanceScheduleFactory(technician=self.technician, status="scheduled")
        self.scheduled_building = BuildingLevelAdhocScheduleFactory(technician=self.technician, status="scheduled")
        
        # Creating overdue jobs
        self.overdue_regular = MaintenanceScheduleFactory(technician=self.technician, status="overdue")
        self.overdue_adhoc = AdHocMaintenanceScheduleFactory(technician=self.technician, status="overdue")
        self.overdue_building = BuildingLevelAdhocScheduleFactory(technician=self.technician, status="overdue")
        
        # Creating completed jobs
        self.completed_regular = MaintenanceScheduleFactory(technician=self.technician, status="completed")
        self.completed_adhoc = AdHocMaintenanceScheduleFactory(technician=self.technician, status="completed")
        self.completed_building = BuildingLevelAdhocScheduleFactory(technician=self.technician, status="completed")
        
    def test_upcoming_jobs(self):
        url = reverse("technician_job_status", args=[self.technician.id, "upcoming_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["regular_schedules"]), 1)
        self.assertEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertEqual(len(response.data["building_adhoc_schedules"]), 1)
        
    def test_overdue_jobs(self):
        url = reverse("technician_job_status", args=[self.technician.id, "overdue_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["regular_schedules"]), 1)
        self.assertEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertEqual(len(response.data["building_adhoc_schedules"]), 1)
        
    def test_completed_jobs(self):
        url = reverse("technician_job_status", args=[self.technician.id, "completed_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["regular_schedules"]), 1)
        self.assertEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertEqual(len(response.data["building_adhoc_schedules"]), 1)
        
    def test_invalid_job_status(self):
        url = reverse("technician_job_status", args=[self.technician.id, "invalid_status"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

