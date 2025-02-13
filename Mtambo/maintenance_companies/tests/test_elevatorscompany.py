import uuid
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from maintenance_companies.models import MaintenanceCompanyProfile
from elevators.models import Elevator
from buildings.models import Building
from developers.models import DeveloperProfile

User = get_user_model()

class ElevatorsUnderCompanyViewTestCase(APITestCase):

    def setUp(self):
        """Setup test data before running tests."""
        self.user = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password",
            first_name="John",
            last_name="Doe",
            account_type="maintenance"
        )

        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="123 Developer Street",
            specialization="Elevators"
        )

        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name="Test Maintenance Company",
            company_address="123 Test Street",
            registration_number="REG12345",
            specialization="Elevators"
        )

        self.building = Building.objects.create(
            name="Test Building",
            address="456 Test Ave",
            contact="9876543210",
            developer=self.developer,
            developer_name="Test Developer"
        )

        self.elevator_1 = Elevator.objects.create(
            user_name="Lift 1",
            controller_type="Digital",
            machine_type="gearless",
            building=self.building,
            machine_number="LIFT001",
            capacity=1000,
            manufacturer="Test Manufacturer",
            installation_date="2023-01-01",
            maintenance_company=self.company,
        )

        self.elevator_2 = Elevator.objects.create(
            user_name="Lift 2",
            controller_type="Analog",
            machine_type="geared",
            building=self.building,
            machine_number="LIFT002",
            capacity=1500,
            manufacturer="Test Manufacturer",
            installation_date="2023-02-01",
            maintenance_company=self.company,
        )

        self.client = APIClient()

    def test_get_elevators_under_company(self):
        """Test retrieving elevators for a maintenance company."""
        url = reverse("maintenance_companies:elevators-under-company", kwargs={"company_id": str(self.company.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)  # We created 2 elevators

        elevator_1_data = data[0]
        self.assertEqual(elevator_1_data["machine_number"], "LIFT001")
        self.assertEqual(elevator_1_data["user_name"], "Lift 1")
        self.assertEqual(elevator_1_data["controller_type"], "Digital")

        elevator_2_data = data[1]
        self.assertEqual(elevator_2_data["machine_number"], "LIFT002")
        self.assertEqual(elevator_2_data["user_name"], "Lift 2")
        self.assertEqual(elevator_2_data["controller_type"], "Analog")

    def test_get_no_elevators_for_company(self):
        """Test API response when no elevators exist for a company."""
        new_user = User.objects.create_user(
            email="new_maintenance@example.com",
            phone_number="0987654321",
            password="password",
            first_name="Jane",
            last_name="Smith",
            account_type="maintenance"
        )

        new_company = MaintenanceCompanyProfile.objects.create(
            user=new_user,
            company_name="New Maintenance Company",
            company_address="789 New Street",
            registration_number="REG67890",
            specialization="Elevators"
        )

        url = reverse("maintenance_companies:elevators-under-company", kwargs={"company_id": str(new_company.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "No elevators found for this building under the specified maintenance company.")

    def test_get_invalid_company_id(self):
        """Test API response for an invalid company UUID."""
        invalid_uuid = uuid.uuid4()
        url = reverse("maintenance_companies:elevators-under-company", kwargs={"company_id": str(invalid_uuid)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "No MaintenanceCompanyProfile matches the given query.")

