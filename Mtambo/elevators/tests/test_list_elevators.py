from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from account.models import User
from buildings.models import Building
from developers.models import DeveloperProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
import uuid

class ElevatorListViewTest(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email="test@example.com",
            phone_number="1234567890",
            password="testpassword",
            first_name="Test",
            last_name="User",
            account_type="developer"
        )
        # Authenticate the user
        self.client.force_authenticate(user=self.user)

        # Create a test developer profile
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="Test Address",
            specialization="Elevators"
        )

        # Create a test building
        self.building = Building.objects.create(
            name="Test Building",
            address="Test Address",
            contact="1234567890",
            developer=self.developer,
            developer_name="Test Developer"
        )

        # Create a test technician
        self.technician = TechnicianProfile.objects.create(
            user=User.objects.create_user(
                email="technician@example.com",
                phone_number="0987654321",
                password="technicianpassword",
                first_name="Technician",
                last_name="User",
                account_type="technician"
            ),
            specialization="Elevator Technician"
        )

        # Create test elevators
        Elevator.objects.create(
            user_name="LIFT1",
            machine_number="ELEV001",
            capacity=1000,
            manufacturer="Otis",
            installation_date="2023-10-01",
            building=self.building,
            technician=self.technician
        )
        Elevator.objects.create(
            user_name="LIFT2",
            machine_number="ELEV002",
            capacity=1500,
            manufacturer="Schindler",
            installation_date="2023-11-01",
            building=self.building
        )

    def test_list_all_elevators(self):
        """
        Test listing all elevators.
        """
        url = reverse('elevator-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # No pagination, so response.data is a list

    def test_filter_elevators_by_building(self):
        """
        Test filtering elevators by building.
        """
        url = reverse('elevator-list')
        response = self.client.get(url, {'building': str(self.building.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # No pagination, so response.data is a list

    def test_filter_elevators_by_machine_type(self):
        """
        Test filtering elevators by machine type.
        """
        url = reverse('elevator-list')
        response = self.client.get(url, {'machine_type': 'gearless'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # No pagination, so response.data is a list

    def test_filter_elevators_by_manufacturer(self):
        """
        Test filtering elevators by manufacturer.
        """
        url = reverse('elevator-list')
        response = self.client.get(url, {'manufacturer': 'Otis'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # No pagination, so response.data is a list
        self.assertEqual(response.data[0]['manufacturer'], "Otis")

    def test_sort_elevators_by_installation_date(self):
        """
        Test sorting elevators by installation date.
        """
        url = reverse('elevator-list')
        response = self.client.get(url, {'ordering': 'installation_date'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['machine_number'], "ELEV001")

    def test_sort_elevators_by_capacity(self):
        """
        Test sorting elevators by capacity.
        """
        url = reverse('elevator-list')
        response = self.client.get(url, {'ordering': '-capacity'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['machine_number'], "ELEV002")
