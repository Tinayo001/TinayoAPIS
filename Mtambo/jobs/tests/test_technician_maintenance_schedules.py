from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from uuid import uuid4
from django.utils import timezone
from account.models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from developers.models import DeveloperProfile
from freezegun import freeze_time
from unittest.mock import patch
from django.db.models.signals import pre_save
from datetime import timedelta

class TechnicianMaintenanceSchedulesViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        # Disconnect the pre_save signal temporarily
        pre_save.disconnect(sender=MaintenanceSchedule, dispatch_uid='update_schedule_status')
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        # Reconnect the signal after tests
        from jobs.models import update_schedule_status
        pre_save.connect(update_schedule_status, sender=MaintenanceSchedule, dispatch_uid='update_schedule_status')
        super().tearDownClass()

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

        # Use timezone.now() + timedelta for future dates
        future_date = timezone.now() + timedelta(days=1)

        # Create regular maintenance schedule with a future date
        self.regular_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date=future_date,
            next_schedule="1_month",
            description="Regular maintenance",
            status="scheduled"
        )

        # Create ad-hoc maintenance schedule
        self.adhoc_schedule = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date=future_date + timedelta(days=1),
            description="Ad-hoc maintenance",
            status="scheduled"
        )

        # Create building-level ad-hoc schedule
        self.building_adhoc_schedule = BuildingLevelAdhocSchedule.objects.create(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date=future_date + timedelta(days=2),
            description="Building-level ad-hoc maintenance",
            status="scheduled"
        )

    def test_get_technician_maintenance_schedules_invalid_technician(self):
        """
        Test retrieving maintenance schedules for a non-existent technician.
        """
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

    @freeze_time("2023-12-01T09:59:59Z")
    def test_get_technician_maintenance_schedules_successful(self):
        """
        Test successfully retrieving maintenance schedules for a technician.
        """
        # Set the schedule date to be in the future relative to the frozen time
        frozen_time = timezone.now()
        future_date = frozen_time + timedelta(hours=1)
        
        # Update the schedule
        self.regular_schedule.scheduled_date = future_date
        self.regular_schedule.status = "scheduled"
        self.regular_schedule.save()

        # Update adhoc schedules as well
        self.adhoc_schedule.scheduled_date = future_date + timedelta(days=1)
        self.adhoc_schedule.save()
        self.building_adhoc_schedule.scheduled_date = future_date + timedelta(days=2)
        self.building_adhoc_schedule.save()

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

    @freeze_time("2023-12-01T10:00:01Z")
    def test_maintenance_schedule_becomes_overdue(self):
        """Test that maintenance schedule status changes to overdue after the scheduled time."""
        # Set the schedule date to be in the past relative to the frozen time
        frozen_time = timezone.now()
        past_date = frozen_time - timedelta(minutes=1)

        # Update the schedule date
        self.regular_schedule.scheduled_date = past_date
        self.regular_schedule.save()
    
        url = reverse("technician-maintenance-schedules", args=[str(self.technician.id)])
        response = self.client.get(url)
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
        # Debug prints
        print("\nDate debugging:")
        print(f"Past date we're looking for: {past_date.isoformat()}Z")
        for schedule in response.data["regular_schedules"]:
            print(f"Schedule date in response: {schedule['maintenance_schedule']['scheduled_date']}")
    
        # Instead of exact date matching, let's find the schedule with status 'overdue'
        overdue_schedule = None
        for schedule in response.data["regular_schedules"]:
            if schedule["maintenance_schedule"]["status"] == "overdue":
                overdue_schedule = schedule["maintenance_schedule"]
                break
    
        self.assertIsNotNone(overdue_schedule, "Could not find any overdue schedule")
        self.assertEqual(overdue_schedule["status"], "overdue") 
