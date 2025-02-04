from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from account.models import User
from buildings.models import Building
from developers.models import DeveloperProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
import uuid

class AddElevatorViewTest(APITestCase):
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

    def test_create_elevator_success(self):
        """
        Test creating an elevator successfully.
        """
        url = reverse('add-elevator')
        data = {
            "user_name": "LIFT1",
            "machine_number": "ELEV001",
            "capacity": 1000,
            "manufacturer": "Otis",
            "installation_date": "2023-10-01",
            "building": str(self.building.id),
            "technician": str(self.technician.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Elevator.objects.count(), 1)
        self.assertEqual(Elevator.objects.get().machine_number, "ELEV001")

    def test_create_elevator_missing_required_fields(self):
        """
        Test creating an elevator with missing required fields.
        """
        url = reverse('add-elevator')
        data = {
            # Missing required fields
            "user_name": "LIFT1",
            "machine_number": "ELEV001",
            "capacity": 1000,
            # Missing "manufacturer", "installation_date", "building"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("manufacturer", response.data)
        self.assertIn("installation_date", response.data)
        self.assertIn("building", response.data)

    def test_create_elevator_invalid_building_uuid(self):
        """
        Test creating an elevator with an invalid building UUID.
        """
        url = reverse('add-elevator')
        data = {
            "user_name": "LIFT1",
            "machine_number": "ELEV001",
            "capacity": 1000,
            "manufacturer": "Otis",
            "installation_date": "2023-10-01",
            "building": "invalid-uuid",  # Invalid UUID
            "technician": str(self.technician.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("building", response.data)

    def test_create_elevator_invalid_technician_uuid(self):
        """
        Test creating an elevator with an invalid technician UUID.
        """
        url = reverse('add-elevator')
        data = {
            "user_name": "LIFT1",
            "machine_number": "ELEV001",
            "capacity": 1000,
            "manufacturer": "Otis",
            "installation_date": "2023-10-01",
            "building": str(self.building.id),
            "technician": "invalid-uuid"  # Invalid UUID
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("technician", response.data)

    def test_create_elevator_duplicate_machine_number(self):
        """
        Test creating an elevator with a duplicate machine number.
        """
        # Create an elevator with the same machine number
        Elevator.objects.create(
            user_name="LIFT1",
            machine_number="ELEV001",
            capacity=1000,
            manufacturer="Otis",
            installation_date="2023-10-01",
            building=self.building
        )

        url = reverse('add-elevator')
        data = {
            "user_name": "LIFT2",
            "machine_number": "ELEV001",  # Duplicate machine number
            "capacity": 1500,
            "manufacturer": "Schindler",
            "installation_date": "2023-11-01",
            "building": str(self.building.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("machine_number", response.data)

    def test_create_elevator_empty_required_fields(self):
        """
        Test creating an elevator with empty required fields.
        """
        url = reverse('add-elevator')
        data = {
            "user_name": "",  # Empty field
            "machine_number": "",  # Empty field
            "capacity": 1000,
            "manufacturer": "Otis",
            "installation_date": "2023-10-01",
            "building": str(self.building.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("user_name", response.data)
        self.assertIn("machine_number", response.data)

    def test_create_elevator_invalid_date_format(self):
        """
        Test creating an elevator with an invalid date format.
        """
        url = reverse('add-elevator')
        data = {
            "user_name": "LIFT1",
            "machine_number": "ELEV001",
            "capacity": 1000,
            "manufacturer": "Otis",
            "installation_date": "2023/10/01",  # Invalid date format
            "building": str(self.building.id)
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("installation_date", response.data)
