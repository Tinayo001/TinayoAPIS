import uuid
from django.test import TestCase
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

    def test_buildings_under_developer_view(self):
        """
        Test the API view that lists buildings under a specific developer and maintenance company.
        """
        url = f"/api/maintenance-companies/buildings/{self.maintenance_company.id}/developer/{self.developer_profile.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("id", response.data[0])
        self.assertEqual(len(response.data), 2)  # Two buildings should be returned

    def test_no_buildings_found(self):
        """
        Test the API view when no buildings are found for the given developer and maintenance company.
        """
        # Create new users for both maintenance company and developer
        user_maintenance_no_building = User.objects.create_user(
            email="maintenance_no_buildings@company.com",
            phone_number="1122334455",
            password="password123",
            first_name="John",
            last_name="NoBuildings",
            account_type="maintenance"
        )

        user_developer_no_building = User.objects.create_user(
            email="developer_no_buildings@company.com",
            phone_number="5544332211",
            password="password123",
            first_name="Bill",
            last_name="Johnson",
            account_type="developer"
        )

        # Create new maintenance company and developer profiles with specialization
        maintenance_company_no_building = MaintenanceCompanyProfile.objects.create(
            user=user_maintenance_no_building,
            company_name="No Buildings Maintenance",
            company_address="No Address",
            registration_number="M654321",
            specialization="Elevators"
        )

        developer_no_building = DeveloperProfile.objects.create(
            user=user_developer_no_building,
            developer_name="No Buildings Developer",
            address="No Address",
            specialization="Commercial"
        )

        url = f"/api/maintenance-companies/buildings/{maintenance_company_no_building.id}/developer/{developer_no_building.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No buildings found.")

    def test_invalid_uuid(self):

        """

        Test the API view when an invalid UUID is provided in the URL.

        """

        # Test with various invalid UUID formats

        invalid_uuids = [

            "invalid-uuid",

            "123",

            "not-a-uuid",

            "12345678-1234-1234-1234-12345678901g"  # invalid character

        ]

        for invalid_uuid in invalid_uuids:

            url = f"/api/maintenance-companies/buildings/{invalid_uuid}/developer/{invalid_uuid}/"

            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertTrue("Invalid UUID format" in response.data["error"])

             

    def test_maintenance_company_not_found(self):
        """
        Test the API view when the maintenance company doesn't exist.
        """
        non_existent_uuid = str(uuid.uuid4())
        url = f"/api/maintenance-companies/buildings/{non_existent_uuid}/developer/{self.developer_profile.id}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Maintenance company not found.")

    def test_developer_not_found(self):
        """
        Test the API view when the developer doesn't exist.
        """
        non_existent_uuid = str(uuid.uuid4())
        url = f"/api/maintenance-companies/buildings/{self.maintenance_company.id}/developer/{non_existent_uuid}/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Developer not found.")
