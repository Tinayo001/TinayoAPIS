from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from datetime import timedelta
from django.utils import timezone
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from jobs.factories import MaintenanceScheduleFactory, AdHocMaintenanceScheduleFactory, BuildingLevelAdhocScheduleFactory, TechnicianProfileFactory

class TechnicianJobStatusViewTest(APITestCase):
    def setUp(self):
        # Create a technician for testing
        self.technician = TechnicianProfileFactory()

        # Create jobs for testing
        self.scheduled_regular = MaintenanceScheduleFactory(status="scheduled", technician=self.technician, scheduled_date=timezone.now() + timedelta(days=1))
        self.scheduled_adhoc = AdHocMaintenanceScheduleFactory(status="scheduled", technician=self.technician, scheduled_date=timezone.now() + timedelta(days=1))
        self.scheduled_building = BuildingLevelAdhocScheduleFactory(status="scheduled", technician=self.technician, scheduled_date=timezone.now() + timedelta(days=1))
        
        self.overdue_regular = MaintenanceScheduleFactory(status="overdue", technician=self.technician, scheduled_date=timezone.now() - timedelta(days=1))
        self.overdue_adhoc = AdHocMaintenanceScheduleFactory(status="overdue", technician=self.technician, scheduled_date=timezone.now() - timedelta(days=1))
        self.overdue_building = BuildingLevelAdhocScheduleFactory(status="overdue", technician=self.technician, scheduled_date=timezone.now() - timedelta(days=1))
        
        self.completed_regular = MaintenanceScheduleFactory(status="completed", technician=self.technician, scheduled_date=timezone.now() - timedelta(days=2))
        self.completed_adhoc = AdHocMaintenanceScheduleFactory(status="completed", technician=self.technician, scheduled_date=timezone.now() - timedelta(days=2))
        self.completed_building = BuildingLevelAdhocScheduleFactory(status="completed", technician=self.technician, scheduled_date=timezone.now() - timedelta(days=2))

    def test_upcoming_jobs(self):
        url = reverse("technician_job_status", args=[self.technician.id, "upcoming_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check the number of upcoming jobs (scheduled)
        scheduled_count = MaintenanceSchedule.objects.filter(status="scheduled", scheduled_date__gte=timezone.now()).count()
        adhoc_count = AdHocMaintenanceSchedule.objects.filter(status="scheduled", scheduled_date__gte=timezone.now()).count()
        building_count = BuildingLevelAdhocSchedule.objects.filter(status="scheduled", scheduled_date__gte=timezone.now()).count()

        self.assertEqual(scheduled_count + adhoc_count + building_count, 3)

    def test_overdue_jobs(self):
        url = reverse("technician_job_status", args=[self.technician.id, "overdue_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check the number of overdue jobs
        scheduled_count = MaintenanceSchedule.objects.filter(status="overdue", scheduled_date__lt=timezone.now()).count()
        adhoc_count = AdHocMaintenanceSchedule.objects.filter(status="overdue", scheduled_date__lt=timezone.now()).count()
        building_count = BuildingLevelAdhocSchedule.objects.filter(status="overdue", scheduled_date__lt=timezone.now()).count()

        self.assertEqual(scheduled_count + adhoc_count + building_count, 3)

    def test_completed_jobs(self):
        url = reverse("technician_job_status", args=[self.technician.id, "completed_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check the number of completed jobs
        scheduled_count = MaintenanceSchedule.objects.filter(status="completed").count()
        adhoc_count = AdHocMaintenanceSchedule.objects.filter(status="completed").count()
        building_count = BuildingLevelAdhocSchedule.objects.filter(status="completed").count()

        self.assertEqual(scheduled_count + adhoc_count + building_count, 3)

