from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from uuid import uuid4
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from developers.models import DeveloperProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule
from technicians.models import TechnicianProfile

class RemoveMaintenanceFromDeveloperElevatorsViewTest(TestCase):
    
    def setUp(self):
        # Create a test user for maintenance
        self.user_maintenance = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password",
            first_name="Maintenance",
            last_name="User",
            account_type="maintenance"
        )

        # Create unique developers with separate User objects
        self.user_developer_1 = User.objects.create_user(
            email="developer1@example.com",
            phone_number="0987654321",
            password="password",
            first_name="Developer1",
            last_name="User",
            account_type="developer"
        )

        self.user_developer_2 = User.objects.create_user(
            email="developer2@example.com",
            phone_number="1122334455",
            password="password",
            first_name="Developer2",
            last_name="User",
            account_type="developer"
        )

        # Create the MaintenanceCompanyProfile for the user
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user_maintenance,
            company_name="Test Maintenance Co."
        )

        # Create DeveloperProfiles for both developers
        self.developer_profile_1 = DeveloperProfile.objects.create(
            user=self.user_developer_1,
            developer_name="Test Developer 1"
        )

        self.developer_profile_2 = DeveloperProfile.objects.create(
            user=self.user_developer_2,
            developer_name="Test Developer 2"
        )

        # Create a Building and Elevators for the first developer
        self.building_1 = Building.objects.create(
            name="Test Building 1",
            address="123 Building St",
            contact="123456789",
            developer=self.developer_profile_1
        )

        self.elevator_1 = Elevator.objects.create(
            user_name="Elevator 1",
            machine_type="gearless",
            building=self.building_1,
            machine_number="LIFT1",
            capacity=1000,
            manufacturer="TestCo",
            installation_date="2024-01-01",
            maintenance_company=self.maintenance_company,
            developer=self.developer_profile_1
        )

        # Create a TechnicianProfile and assign it to the elevator
        self.technician = TechnicianProfile.objects.create(
            user=self.user_maintenance,
            maintenance_company=self.maintenance_company,
            is_approved=True
        )
        
        # Create a MaintenanceSchedule linked to the elevator
        self.schedule_1 = MaintenanceSchedule.objects.create(
            elevator=self.elevator_1,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2025-01-25T10:00:00Z",
            next_schedule="1_month",
            description="Elevator inspection",
            status="scheduled"
        )

        # Initialize the API client
        self.client = APIClient()

    def test_remove_maintenance_from_developer_elevators(self):
        url = reverse('maintenance_companies:remove-maintenance-from-developer-elevators', 
                     kwargs={'company_id': self.maintenance_company.id,
                            'developer_id': self.developer_profile_1.id})
        response = self.client.delete(url)

        # Verify the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that the maintenance company and technician were removed from the elevator
        self.elevator_1.refresh_from_db()
        self.assertIsNone(self.elevator_1.maintenance_company)
        self.assertIsNone(self.elevator_1.technician)

        # Verify that the maintenance company and technician were removed from the schedule
        self.schedule_1.refresh_from_db()
        self.assertIsNone(self.schedule_1.maintenance_company)
        self.assertIsNone(self.schedule_1.technician)

    def test_no_buildings_for_developer(self):
        # Create a new user for this test
        user_developer_3 = User.objects.create_user(
            email="developer3@example.com",
            phone_number="9876543210",
            password="password",
            first_name="Developer3",
            last_name="User",
            account_type="developer"
        )

        # Create a new developer with no buildings
        new_developer = DeveloperProfile.objects.create(
            user=user_developer_3,
            developer_name="No Buildings Developer"
        )

        url = reverse('maintenance_companies:remove-maintenance-from-developer-elevators', 
                     kwargs={'company_id': self.maintenance_company.id,
                            'developer_id': new_developer.id})
        response = self.client.delete(url)

        # Verify the response status and message
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No buildings found for this developer", response.data['message'])

    def test_no_elevators_linked_to_maintenance_company(self):
        # Create a new user for this test
        user_developer_4 = User.objects.create_user(
            email="developer4@example.com",
            phone_number="0123456789",
            password="password",
            first_name="Developer4",
            last_name="User",
            account_type="developer"
        )

        # Create a new developer with buildings but no elevators linked to the maintenance company
        new_developer = DeveloperProfile.objects.create(
            user=user_developer_4,
            developer_name="No Elevators Developer"
        )
    
        new_building = Building.objects.create(
            name="No Elevators Building",
            address="456 Building St",
            contact="987654321",
            developer=new_developer
        )

        url = reverse('maintenance_companies:remove-maintenance-from-developer-elevators', 
                     kwargs={'company_id': self.maintenance_company.id,
                            'developer_id': new_developer.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No elevators found for this developer.", response.data['message'])
    
    def test_invalid_maintenance_company(self):
        url = reverse('maintenance_companies:remove-maintenance-from-developer-elevators', 
                     kwargs={'company_id': uuid4(),
                            'developer_id': self.developer_profile_1.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Maintenance company not found", response.data['error'])

    def test_invalid_developer(self):
        url = reverse('maintenance_companies:remove-maintenance-from-developer-elevators', 
                     kwargs={'company_id': self.maintenance_company.id,
                            'developer_id': uuid4()})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Developer not found", response.data['error'])
