from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from jobs.factories import (
    MaintenanceCompanyProfileFactory,
    MaintenanceScheduleFactory,
    AdHocMaintenanceScheduleFactory,
    BuildingLevelAdhocScheduleFactory,
)

class MaintenanceCompanyJobStatusViewTest(APITestCase):
    def setUp(self):
        self.maintenance_company = MaintenanceCompanyProfileFactory()
        self.base_url = "maintenance-company/{}/jobs/{{}}/".format(self.maintenance_company.id)

        # Create maintenance schedules
        self.upcoming_regular = MaintenanceScheduleFactory(maintenance_company=self.maintenance_company, status="scheduled")
        self.overdue_regular = MaintenanceScheduleFactory(maintenance_company=self.maintenance_company, status="overdue")
        self.completed_regular = MaintenanceScheduleFactory(maintenance_company=self.maintenance_company, status="completed")

        # Create ad-hoc schedules
        self.upcoming_adhoc = AdHocMaintenanceScheduleFactory(maintenance_company=self.maintenance_company, status="scheduled")
        self.overdue_adhoc = AdHocMaintenanceScheduleFactory(maintenance_company=self.maintenance_company, status="overdue")
        self.completed_adhoc = AdHocMaintenanceScheduleFactory(maintenance_company=self.maintenance_company, status="completed")

        # Create building-level ad-hoc schedules
        self.upcoming_building_adhoc = BuildingLevelAdhocScheduleFactory(maintenance_company=self.maintenance_company, status="scheduled")
        self.overdue_building_adhoc = BuildingLevelAdhocScheduleFactory(maintenance_company=self.maintenance_company, status="overdue")
        self.completed_building_adhoc = BuildingLevelAdhocScheduleFactory(maintenance_company=self.maintenance_company, status="completed")

    def test_get_upcoming_jobs(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "upcoming_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["regular_schedules"]), 1)
        self.assertEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertEqual(len(response.data["building_adhoc_schedules"]), 1)

    def test_get_overdue_jobs(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "overdue_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["regular_schedules"]), 1)
        self.assertEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertEqual(len(response.data["building_adhoc_schedules"]), 1)

    def test_get_completed_jobs(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "completed_jobs"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["regular_schedules"]), 1)
        self.assertEqual(len(response.data["adhoc_schedules"]), 1)
        self.assertEqual(len(response.data["building_adhoc_schedules"]), 1)

    def test_invalid_job_status(self):
        url = reverse("maintenance_company_job_status", args=[self.maintenance_company.id, "invalid_status"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid job_status provided", response.data["detail"])

