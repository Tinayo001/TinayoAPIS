from uuid import uuid4
from django.test import TestCase
from rest_framework import status
from django.urls import reverse
from account.models import User
from developers.models import DeveloperProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile


class DeveloperMaintenanceSchedulesViewTest(TestCase):
    """
    Test the retrieval of maintenance schedules for a developer.
    """
    def setUp(self):
        """
        Set up test data (Users, DeveloperProfiles, Buildings, Elevators, MaintenanceSchedules, etc.)
        """
        # Create test User (Developer)
        user = User.objects.create_user(
            email="testdeveloper@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="Test",
            last_name="Developer",
            account_type="developer"
        )
        
        # Create DeveloperProfile for the user
        self.developer_profile = DeveloperProfile.objects.create(
            user=user,
            developer_name="Test Developer",
            address="123 Developer St",
            specialization="Elevators"
        )

        # Create a Building linked to the DeveloperProfile
        self.building = Building.objects.create(
            name="Test Building",
            address="123 Building St",
            contact="1234567890",
            developer=self.developer_profile
        )

        # Create Elevator linked to the Building
        self.elevator = Elevator.objects.create(
            user_name="Elevator 1",
            machine_type="gearless",
            building=self.building,
            machine_number="E123",
            capacity=1000,
            manufacturer="ElevatorCo",
            installation_date="2020-01-01",
            developer=self.developer_profile
        )

        # Create a MaintenanceCompanyProfile for testing (required for schedules)
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=user,
            company_name="Test Maintenance Co.",
            company_address="123 Maintenance St.",
            registration_number="TEST123",
            specialization="Elevators"
        )

        # Create a TechnicianProfile for testing
        self.technician = TechnicianProfile.objects.create(
            user=user,  # Link technician to the user
            specialization="Elevator Technician",  # Set the technician's specialization
            is_approved=True  # Set technician approval status (optional)
        )

        # Create MaintenanceSchedule for the elevator with maintenance company and technician
        self.maintenance_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2025-02-01 10:00:00",
            next_schedule="1_month",
            description="Routine maintenance",
            status="scheduled"
        )

        # Create AdHocMaintenanceSchedule for the elevator with maintenance company and technician
        self.ad_hoc_schedule = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2025-02-01 12:00:00",
            description="Emergency repair",
            status="scheduled"
        )

        # URL to access maintenance schedules for a developer
        self.url = reverse('developer-maintenance-schedules', kwargs={'developer_id': self.developer_profile.id})

    def test_get_maintenance_schedules_for_developer(self):
        """
        Test retrieving maintenance schedules for a developer.
        """
        # Make GET request to the API endpoint
        response = self.client.get(self.url)

        # Check if the response is successful (status code 200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the response contains the expected structure
        self.assertIn("regular_schedules", response.data)
        self.assertIn("adhoc_schedules", response.data)

        # Verify the data matches the expected maintenance schedule info
        regular_schedules = response.data["regular_schedules"]
        adhoc_schedules = response.data["adhoc_schedules"]

        # Adjusted to access the correct key path
        self.assertEqual(len(regular_schedules), 1)
        self.assertEqual(regular_schedules[0]["maintenance_schedule"]["description"], "Routine maintenance")
        self.assertEqual(len(adhoc_schedules), 1)
        self.assertEqual(adhoc_schedules[0]["maintenance_schedule"]["description"], "Emergency repair")
     
     

    def test_developer_not_found(self):
        """
        Test that a 404 error is returned when the developer does not exist.
        """
        # Use a random UUID that does not exist
        non_existent_developer_id = uuid4()

        # Make GET request with a non-existent developer ID
        url = reverse('developer-maintenance-schedules', kwargs={'developer_id': non_existent_developer_id})
        response = self.client.get(url)

        # Check if the response is a 404 (developer not found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_buildings_for_developer(self):
        """
        Test that a 404 error is returned when no buildings are associated with the developer.
        """
        # Create a new developer without any buildings
        user = User.objects.create_user(
            email="anotherdeveloper@example.com",
            phone_number="9876543210",
            password="password123",
            first_name="Another",
            last_name="Developer",
            account_type="developer"
        )
        
        developer_profile = DeveloperProfile.objects.create(
            user=user,
            developer_name="Another Developer",
            address="123 Developer Rd",
            specialization="Elevators"
        )

        # Use this developer ID in the URL
        url = reverse('developer-maintenance-schedules', kwargs={'developer_id': developer_profile.id})

        # Make GET request to the API endpoint
        response = self.client.get(url)

        # Check if the response is a 404 (no buildings found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_no_elevators_for_developer(self):
        """
        Test that a 404 error is returned when no elevators are associated with the developer.
        """
        # Create another developer profile with a building but no elevators
        user = User.objects.create_user(
            email="thirddeveloper@example.com",
            phone_number="1122334455",
            password="password123",
            first_name="Third",
            last_name="Developer",
            account_type="developer"
        )
        
        developer_profile = DeveloperProfile.objects.create(
            user=user,
            developer_name="Third Developer",
            address="456 Developer Ln",
            specialization="Elevators"
        )

        building = Building.objects.create(
            name="Third Building",
            address="456 Building Ln",
            contact="1122334455",
            developer=developer_profile
        )

        # Use this developer ID in the URL
        url = reverse('developer-maintenance-schedules', kwargs={'developer_id': developer_profile.id})

        # Make GET request to the API endpoint
        response = self.client.get(url)

        # Check if the response is a 404 (no elevators found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

