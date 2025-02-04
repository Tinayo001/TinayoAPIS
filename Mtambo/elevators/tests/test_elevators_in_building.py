import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from buildings.models import Building
from developers.models import DeveloperProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
from account.models import User

User = get_user_model()

class ElevatorsInBuildingViewTest(APITestCase):
    def setUp(self):
        """
        Set up test data.
        """
        # Create a user
        self.user = User.objects.create_user(
            email="test@example.com",
            phone_number="1234567890",
            first_name="Test",
            last_name="User",
            password="testpassword",
            account_type="developer"
        )

        # Create a developer profile
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="123 Developer Street",
            specialization="Elevators"
        )

        # Create a building
        self.building = Building.objects.create(
            name="Test Building",
            address="123 Test Street",
            contact="123-456-7890",
            developer=self.developer
        )

        # Create a maintenance company
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name="Test Maintenance Company",
            company_address="123 Maintenance Street",
            registration_number="TEST123",
            specialization="Elevators"
        )

        # Create a technician
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            specialization="Elevator Technician",
            maintenance_company=self.maintenance_company,
            is_approved=True
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
            developer=self.developer,
            technician=self.technician
        )

    def test_retrieve_elevators_in_building(self):
        """
        Test retrieving elevators in a building (happy path).
        """
        url = reverse('elevators-in-building', args=[self.building.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user_name'], self.elevator.user_name)

    def test_retrieve_elevators_in_nonexistent_building(self):
        """
        Test retrieving elevators in a building that does not exist.
        """
        nonexistent_building_id = uuid.uuid4()
        url = reverse('elevators-in-building', args=[nonexistent_building_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Building not found.")

    def test_retrieve_elevators_in_building_with_no_elevators(self):
        """
        Test retrieving elevators in a building with no elevators.
        """
        # Create a new building with no elevators
        new_building = Building.objects.create(
            name="Empty Building",
            address="456 Empty Street",
            contact="987-654-3210",
            developer=self.developer
        )

        url = reverse('elevators-in-building', args=[new_building.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "No elevators found for this building.")
