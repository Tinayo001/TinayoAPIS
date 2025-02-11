from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from datetime import datetime
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from jobs.factories import (
    MaintenanceCompanyProfileFactory,
    MaintenanceScheduleFactory,
    AdHocMaintenanceScheduleFactory,
    BuildingLevelAdhocScheduleFactory,
)

class MaintenanceCompanyJobStatusViewTest(APITestCase):
    def setUp(self):
        # Clear all existing schedules before running tests
        MaintenanceSchedule.objects.all().delete()
        AdHocMaintenanceSchedule.objects.all().delete()
        BuildingLevelAdhocSchedule.objects.all().delete()

        self.maintenance_company = MaintenanceCompanyProfileFactory()
        self.base_url = "maintenance-company/{}/jobs/{{}}/".format(self.maintenance_company.id)

        # Set up timezone-aware scheduled dates
        now = timezone.now()
        future_date = now + timezone.timedelta(days=10)
        past_date = now - timezone.timedelta(days=10)

        # Create upcoming (future) schedules
        self.upcoming_regular = MaintenanceScheduleFactory(
            maintenance_company=self.maintenance_company, status="scheduled", scheduled_date=future_date
        )
        self.upcoming_adhoc = AdHocMaintenanceScheduleFactory(
            maintenance_company=self.maintenance_company, status="scheduled", scheduled_date=future_date
        )
        self.upcoming_building_adhoc = BuildingLevelAdhocScheduleFactory(
            maintenance_company=self.maintenance_company, status="scheduled", scheduled_date=future_date
        )

        # Create overdue (past) schedules
        self.overdue_regular = MaintenanceScheduleFactory(
            maintenance_company=self.maintenance_company, status="overdue", scheduled_date=past_date
        )
        self.overdue_adhoc = AdHocMaintenanceScheduleFactory(
            maintenance_company=self.maintenance_company, status="overdue", scheduled_date=past_date
        )
        self.overdue_building_adhoc = BuildingLevelAdhocScheduleFactory(
            maintenance_company=self.maintenance_company, status="overdue", scheduled_date=past_date
        )

        # Create completed schedules
        self.completed_regular = MaintenanceScheduleFactory(
            maintenance_company=self.maintenance_company, status="completed", scheduled_date=past_date
        )
        self.completed_adhoc = AdHocMaintenanceScheduleFactory(
            maintenance_company=self.maintenance_company, status="completed", scheduled_date=past_date
        )
        self.completed_building_adhoc = BuildingLevelAdhocScheduleFactory(
            maintenance_company=self.maintenance_company, status="completed", scheduled_date=past_date
        )

    def test_get_upcoming_jobs(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "upcoming_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        print("Response data for upcoming_jobs:", response.data)  # Debugging

        self.assertGreaterEqual(len(response.data["regular_schedules"]), 1)
        self.assertGreaterEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertGreaterEqual(len(response.data["building_adhoc_schedules"]), 1)

    def test_get_overdue_jobs(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "overdue_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        print("Response data for overdue_jobs:", response.data)  # Debugging

        self.assertGreaterEqual(len(response.data["regular_schedules"]), 1)
        self.assertGreaterEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertGreaterEqual(len(response.data["building_adhoc_schedules"]), 1)

    def test_get_completed_jobs(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "completed_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        print("Response data for completed_jobs:", response.data)  # Debugging

        self.assertGreaterEqual(len(response.data["regular_schedules"]), 1)
        self.assertGreaterEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertGreaterEqual(len(response.data["building_adhoc_schedules"]), 1)

    def test_invalid_job_status(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "invalid_status"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid job_status provided", response.data["detail"])

