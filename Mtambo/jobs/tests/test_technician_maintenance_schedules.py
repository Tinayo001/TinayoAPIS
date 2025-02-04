from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from uuid import uuid4
from account.models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from developers.models import DeveloperProfile


class TechnicianMaintenanceSchedulesViewTests(TestCase):
    def setUp(self):
        """
        Set up test data for all test methods.
        """
        self.client = APIClient()

        # Create a user for the technician
        self.user = User.objects.create_user(
            email="technician@example.com",
            phone_number="1234567890",
            first_name="John",
            last_name="Doe",
            password="password123",
            account_type="technician"
        )

        # Create a user for the developer
        self.developer_user = User.objects.create_user(
            email="developer@example.com",
            phone_number="0987654321",
            first_name="Jane",
            last_name="Smith",
            password="password123",
            account_type="developer"
        )

        # Create a developer profile
        self.developer = DeveloperProfile.objects.create(
            user=self.developer_user,
            developer_name="Test Developer",
            address="123 Developer St",
            specialization="Elevators"
        )

        # Create a maintenance company
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name="Test Maintenance Company",
            company_address="123 Test St",
            registration_number="TEST123",
            specialization="Elevators"
        )

        # Create a technician profile
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            specialization="Elevator Maintenance",
            maintenance_company=self.maintenance_company
        )

        # Create a building
        self.building = Building.objects.create(
            name="Test Building",
            address="456 Test Ave",
            contact="9876543210",
            developer=self.developer
        )

        # Create an elevator
        self.elevator = Elevator.objects.create(
            user_name="LIFT1",
            controller_type="Digital",
            machine_type="gearless",
            building=self.building,
            machine_number="ELEV001",
            capacity=1000,
            manufacturer="Test Manufacturer",
            installation_date="2023-01-01",
            maintenance_company=self.maintenance_company,
            technician=self.technician
        )

        # Create maintenance schedules
        self.regular_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2023-12-01T10:00:00Z",
            next_schedule="1_month",
            description="Regular maintenance",
            status="scheduled"
        )

        self.adhoc_schedule = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2023-12-05T10:00:00Z",
            description="Ad-hoc maintenance",
            status="scheduled"
        )

        self.building_adhoc_schedule = BuildingLevelAdhocSchedule.objects.create(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2023-12-10T10:00:00Z",
            description="Building-level ad-hoc maintenance",
            status="scheduled"
        )

    def test_get_technician_maintenance_schedules_successful(self):
        """
        Test successfully retrieving maintenance schedules for a technician.
        """
        url = reverse("technician-maintenance-schedules", args=[str(self.technician.id)])
        response = self.client.get(url)

        # Assert response status and structure
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("regular_schedules", response.data)
        self.assertIn("adhoc_schedules", response.data)
        self.assertIn("building_adhoc_schedules", response.data)

        # Check regular schedules
        self.assertEqual(len(response.data["regular_schedules"]), 1)
        regular_schedule = response.data["regular_schedules"][0]["maintenance_schedule"]
        self.assertEqual(regular_schedule["id"], str(self.regular_schedule.id))
        self.assertEqual(regular_schedule["status"], "scheduled")
        self.assertEqual(regular_schedule["description"], "Regular maintenance")

        # Check ad-hoc schedules
        self.assertEqual(len(response.data["adhoc_schedules"]), 1)
        adhoc_schedule = response.data["adhoc_schedules"][0]["maintenance_schedule"]
        self.assertEqual(adhoc_schedule["id"], str(self.adhoc_schedule.id))
        self.assertEqual(adhoc_schedule["status"], "scheduled")
        self.assertEqual(adhoc_schedule["description"], "Ad-hoc maintenance")

        # Check building-level ad-hoc schedules
        self.assertEqual(len(response.data["building_adhoc_schedules"]), 1)
        building_schedule = response.data["building_adhoc_schedules"][0]
        self.assertEqual(building_schedule["id"], str(self.building_adhoc_schedule.id))
        self.assertEqual(building_schedule["status"], "scheduled")
        self.assertEqual(building_schedule["description"], "Building-level ad-hoc maintenance")

    def test_get_technician_maintenance_schedules_invalid_technician(self):
        """
        Test retrieving maintenance schedules for a non-existent technician.
        """
        # Use a valid UUID format that doesn't exist in the database
        invalid_technician_id = uuid4()
        url = reverse("technician-maintenance-schedules", args=[str(invalid_technician_id)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Technician not found.")

    def test_get_technician_maintenance_schedules_no_schedules(self):
        """
        Test retrieving maintenance schedules for a technician with no schedules.
        """
        # Delete all schedules
        MaintenanceSchedule.objects.all().delete()
        AdHocMaintenanceSchedule.objects.all().delete()
        BuildingLevelAdhocSchedule.objects.all().delete()

        url = reverse("technician-maintenance-schedules", args=[str(self.technician.id)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "No maintenance schedules found for this technician.")

    def test_maintenance_schedule_data_structure(self):
        """
        Test the detailed structure of the maintenance schedule response data.
        """
        url = reverse("technician-maintenance-schedules", args=[str(self.technician.id)])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Test regular schedule structure
        regular_schedule = response.data["regular_schedules"][0]["maintenance_schedule"]
        self.assertIn("elevator", regular_schedule)
        self.assertIn("technician", regular_schedule)
        self.assertIn("maintenance_company", regular_schedule)
        self.assertIn("scheduled_date", regular_schedule)
        self.assertIn("description", regular_schedule)
        self.assertIn("status", regular_schedule)

        # Test elevator details in regular schedule
        elevator_details = regular_schedule["elevator"]
        self.assertIn("id", elevator_details)
        self.assertIn("user_name", elevator_details)
        self.assertIn("machine_number", elevator_details)
        self.assertEqual(elevator_details["user_name"], "LIFT1")
        self.assertEqual(elevator_details["machine_number"], "ELEV001")

        # Test building details in regular schedule
        self.assertIn("building", regular_schedule)
        building_details = regular_schedule["building"]
        self.assertIn("id", building_details)
        self.assertIn("name", building_details)
        self.assertEqual(building_details["name"], "Test Building")
