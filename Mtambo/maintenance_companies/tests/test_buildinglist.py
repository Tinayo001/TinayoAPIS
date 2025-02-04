from datetime import date
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from buildings.models import Building
from elevators.models import Elevator
from developers.models import DeveloperProfile  # Import DeveloperProfile
import uuid

class BuildingListViewTest(APITestCase):

    def setUp(self):
        # Create a user for maintenance company
        self.user = User.objects.create_user(
            email="testuser@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="Test",
            last_name="User",
            account_type="maintenance"
        )

        # Create a developer profile
        self.developer_user = User.objects.create_user(
            email="developer@example.com",
            phone_number="0987654321",
            password="password123",
            first_name="Dev",
            last_name="User",
            account_type="developer"
        )
        self.developer = DeveloperProfile.objects.create(
            id=uuid.uuid4(),
            user=self.developer_user,
            developer_name="Test Developer",
            address="456 Developer Street",
            specialization="Residential Buildings"
        )

        # Create a maintenance company for this user
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            id=uuid.uuid4(),
            user=self.user,  # Associate with a unique user
            company_name="Test Maintenance Company",
            company_address="123 Test Street",
            registration_number="TEST123",
            specialization="Elevators"
        )

        # Create buildings linked to the developer
        self.building1 = Building.objects.create(
            name="Building 1",
            address="Address 1",
            developer_name=self.developer.developer_name,
            developer=self.developer  # Link the developer
        )
        self.building2 = Building.objects.create(
            name="Building 2",
            address="Address 2",
            developer_name=self.developer.developer_name,
            developer=self.developer  # Link the developer
        )

        # Link buildings to elevators (Ensure unique machine_number)
        self.elevator1 = Elevator.objects.create(
            building=self.building1,
            capacity=10,
            maintenance_company=self.maintenance_company,
            installation_date=date.today(),
            machine_number="MACH_001"  # Unique machine_number
        )
        self.elevator2 = Elevator.objects.create(
            building=self.building2,
            capacity=10,
            maintenance_company=self.maintenance_company,
            installation_date=date.today(),
            machine_number="MACH_002"  # Unique machine_number
        )

        # Use reverse with proper namespace (if applicable)
        self.url = reverse('maintenance_companies:building-list', kwargs={'company_id': self.maintenance_company.id})

    def test_get_buildings_success(self):
        """Test retrieving buildings linked to a maintenance company."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        building_names = [building['name'] for building in response.data]
        self.assertIn("Building 1", building_names)
        self.assertIn("Building 2", building_names)

    def test_get_buildings_no_company(self):
        """Test retrieving buildings for a non-existent company."""
        invalid_url = reverse('maintenance_companies:building-list', kwargs={'company_id': uuid.uuid4()})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Maintenance company not found.")

    def test_get_buildings_no_linked_buildings(self):
        """Test retrieving buildings when the company has no linked buildings."""
        # Create a unique user for the new maintenance company to avoid constraint error
        new_user = User.objects.create_user(
            email="newuser@example.com",
            phone_number="9876543210",
            password="password123",
            first_name="New",
            last_name="User",
            account_type="maintenance"
        )

        # Create a new maintenance company with no linked buildings
        new_company = MaintenanceCompanyProfile.objects.create(
            id=uuid.uuid4(),
            user=new_user,  # Use a different user to avoid constraint violation
            company_name="New Maintenance Company",
            company_address="456 New Street",
            registration_number="NEW456",
            specialization="HVAC"
        )

        new_url = reverse('maintenance_companies:building-list', kwargs={'company_id': new_company.id})
        response = self.client.get(new_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "No buildings found for this maintenance company.")

    def test_invalid_method(self):
        """Test that invalid HTTP methods return the correct response."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

