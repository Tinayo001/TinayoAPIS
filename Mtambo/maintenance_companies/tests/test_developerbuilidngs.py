import uuid
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from developers.models import DeveloperProfile
from buildings.models import Building
from elevators.models import Elevator

class BuildingsUnderDeveloperViewTest(TestCase):
    def setUp(self):
        """
        Set up the test data: Create users, developer, maintenance company, buildings, and elevators.
        """
        # Create a user (maintenance company owner)
        self.user_maintenance = User.objects.create_user(
            email="maintenance@company.com",
            phone_number="1234567890",
            password="password123",
            first_name="John",
            last_name="Doe",
            account_type="maintenance"
        )

        # Create a user (developer)
        self.user_developer = User.objects.create_user(
            email="developer@company.com",
            phone_number="0987654321",
            password="password123",
            first_name="Jane",
            last_name="Smith",
            account_type="developer"
        )

        # Create a Maintenance Company profile
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user_maintenance,
            company_name="Elevator Maintenance Co.",
            company_address="123 Main St, City, Country",
            registration_number="M123456",
            specialization="Elevators"
        )

        # Create a Developer profile
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.user_developer,
            developer_name="Skyline Developers",
            address="456 Developer Ave, City, Country",
            specialization="Residential"
        )

        # Create Buildings for the developer
        self.building_1 = Building.objects.create(
            name="Skyline Tower",
            address="789 High St, City, Country",
            contact="contact@skyline.com",
            developer=self.developer_profile,
            developer_name="Skyline Developers"
        )

        self.building_2 = Building.objects.create(
            name="Skyline Heights",
            address="101 Heights St, City, Country",
            contact="contact@heights.com",
            developer=self.developer_profile,
            developer_name="Skyline Developers"
        )

        # Create Elevators for the buildings
        self.elevator_1 = Elevator.objects.create(
            user_name="LIFT001",
            controller_type="Digital",
            machine_type="gearless",
            building=self.building_1,
            machine_number="LIFT001",
            capacity=1000,
            manufacturer="Elevator Co.",
            installation_date="2022-01-01",
            maintenance_company=self.maintenance_company,
            developer=self.developer_profile
        )

        self.elevator_2 = Elevator.objects.create(
            user_name="LIFT002",
            controller_type="Analog",
            machine_type="geared",
            building=self.building_2,
            machine_number="LIFT002",
            capacity=1500,
            manufacturer="LiftTech",
            installation_date="2023-02-01",
            maintenance_company=self.maintenance_company,
            developer=self.developer_profile
        )

        # Initialize the APIClient
        self.client = APIClient()

    def get_url(self, company_id, developer_id):
        """Helper method to generate the URL with proper reverse lookup"""
        return reverse('maintenance_companies:buildings-under-developer', 
                      kwargs={
                          'company_id': str(company_id),
                          'developer_id': str(developer_id)
                      })

    def test_get_buildings_success(self):
        """Test successful retrieval of buildings"""
        url = self.get_url(self.maintenance_company.id, self.developer_profile.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Two buildings should be returned
        
        # Verify building data structure
        for building in response.data:
            self.assertIn('name', building)
            self.assertIn('address', building)
            self.assertIn('contact', building)
            self.assertIn('developer', building)  # Check if 'developer' is present
            self.assertIn('developer_name', building['developer'])  # Check 'developer_name' within the 'developer' key

    def test_get_buildings_no_buildings_found(self):
        """Test when no buildings are found"""
        # Create new profiles without buildings
        new_maintenance = MaintenanceCompanyProfile.objects.create(
            user=User.objects.create_user(
                email="new_maintenance@test.com",
                phone_number="9999999999",
                password="password123",
                account_type="maintenance"
            ),
            company_name="New Maintenance Co",
            company_address="New Address",
            registration_number="NEW123",
            specialization="Elevators"
        )

        new_developer = DeveloperProfile.objects.create(
            user=User.objects.create_user(
                email="new_developer@test.com",
                phone_number="8888888888",
                password="password123",
                account_type="developer"
            ),
            developer_name="New Developer",
            address="New Address",
            specialization="Commercial"
        )

        url = self.get_url(new_maintenance.id, new_developer.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            response.data["message"], 
            "No buildings found for this developer and maintenance company."
        )

    def test_get_buildings_invalid_uuid(self):
        """Test with invalid UUID format"""
        response = self.client.get(
            f"/api/maintenance-companies/not-a-uuid/developers/{self.developer_profile.id}/buildings/"
        )
    
        # Check for 404 status code
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
        # Since the response is a Not Found error, check the content for error message
        self.assertIn("Not Found", response.content.decode())
    
    def test_get_buildings_maintenance_company_not_found(self):
        """Test with non-existent maintenance company"""
        non_existent_uuid = uuid.uuid4()
        url = self.get_url(non_existent_uuid, self.developer_profile.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Maintenance company not found.")

    def test_get_buildings_developer_not_found(self):
        """Test with non-existent developer"""
        non_existent_uuid = uuid.uuid4()
        url = self.get_url(self.maintenance_company.id, non_existent_uuid)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Developer not found.")

