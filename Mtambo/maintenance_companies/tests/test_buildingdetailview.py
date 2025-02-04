from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from uuid import uuid4
from datetime import date
from maintenance_companies.models import MaintenanceCompanyProfile
from buildings.models import Building
from account.models import User
from developers.models import DeveloperProfile
from elevators.models import Elevator

class BuildingDetailViewTest(TestCase):

    def setUp(self):
        # Create unique users for testing
        self.maintenance_user = User.objects.create_user(
            email="maintenanceuser@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="Test",
            last_name="User",
            account_type="maintenance"
        )

        self.developer_user = User.objects.create_user(
            email="developer@example.com",
            phone_number="0987654321",
            password="password123",
            first_name="Dev",
            last_name="User",
            account_type="developer"
        )

        # Create developer profile
        self.developer = DeveloperProfile.objects.create(
            user=self.developer_user,
            developer_name="Test Developer",
            address="456 Developer Street",
            specialization="Residential Buildings"
        )

        # Create maintenance company and link to maintenance user
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name="Test Maintenance Company",
            company_address="123 Test Street",
            registration_number="TEST123",
            specialization="Elevators"
        )

        # Create buildings linked to the developer
        self.building1 = Building.objects.create(
            name="Building 1",
            address="Address 1",
            contact="1234567890",
            developer=self.developer,
            developer_name=self.developer.developer_name
        )
        self.building2 = Building.objects.create(
            name="Building 2",
            address="Address 2",
            contact="0987654321",
            developer=self.developer,
            developer_name=self.developer.developer_name
        )

        # Create elevator to link building1 with maintenance company
        self.elevator = Elevator.objects.create(
            user_name="LIFT1",
            controller_type="Digital",
            machine_type="gearless",
            building=self.building1,
            machine_number="TEST001",
            capacity=1000,
            manufacturer="Test Manufacturer",
            installation_date=date.today(),
            maintenance_company=self.maintenance_company,
            developer=self.developer
        )

        # Set up the API client
        self.client = APIClient()

    def test_get_building_success(self):
        """Test retrieving building details successfully when linked to maintenance company."""
        url = reverse('maintenance_companies:building-detail', 
                     kwargs={'company_id': self.maintenance_company.id, 
                            'building_id': self.building1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.building1.name)
        self.assertEqual(response.data['address'], self.building1.address)

    def test_get_building_company_not_found(self):
        """Test retrieving building details when the maintenance company does not exist."""
        invalid_company_id = uuid4()
        url = reverse('maintenance_companies:building-detail', 
                     kwargs={'company_id': invalid_company_id, 
                            'building_id': self.building1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Maintenance company not found.")

    def test_get_building_building_not_found(self):
        """Test retrieving building details when the building does not exist."""
        invalid_building_id = uuid4()
        url = reverse('maintenance_companies:building-detail', 
                     kwargs={'company_id': self.maintenance_company.id, 
                            'building_id': invalid_building_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Building not found.")

    def test_get_building_not_linked_to_company(self):
        """Test retrieving building details when the building is not linked to the maintenance company."""
        url = reverse('maintenance_companies:building-detail', 
                     kwargs={'company_id': self.maintenance_company.id, 
                            'building_id': self.building2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Building is not linked to the specified maintenance company.")

    def test_get_building_unexpected_error(self):
        """Test unexpected error handling."""
        url = reverse('maintenance_companies:building-detail', 
                     kwargs={'company_id': self.maintenance_company.id, 
                            'building_id': uuid4()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Building not found.")

    def test_invalid_method(self):
        """Test that invalid HTTP methods return the correct response."""
        url = reverse('maintenance_companies:building-detail', 
                     kwargs={'company_id': self.maintenance_company.id, 
                            'building_id': self.building1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
