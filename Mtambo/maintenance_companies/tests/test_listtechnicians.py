from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from account.models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
import uuid


class MaintenanceCompanyTechniciansViewTest(APITestCase):
    def setUp(self):
        """Set up test data for maintenance company and technician profiles."""
        # Create a maintenance company user and profile
        self.maintenance_user = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password123",
            account_type="maintenance",  # Assuming TextChoices for account_type
        )
        self.maintenance_profile = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name="Test Maintenance Co",
            company_address="123 Test St",
            registration_number="REG123",
            specialization="Elevators",
        )

        # Create technician users and profiles
        self.tech1_user = User.objects.create_user(
            email="tech1@example.com",
            phone_number="9876543210",
            password="password123",
            account_type="technician",
        )
        self.tech1_profile = TechnicianProfile.objects.create(
            user=self.tech1_user,
            specialization="Elevators",
            maintenance_company=self.maintenance_profile,
            is_approved=True,
        )

        self.tech2_user = User.objects.create_user(
            email="tech2@example.com",
            phone_number="5555555555",
            password="password123",
            account_type="technician",
        )
        self.tech2_profile = TechnicianProfile.objects.create(
            user=self.tech2_user,
            specialization="Generators",
            maintenance_company=self.maintenance_profile,
            is_approved=True,
        )

        # Define URL for listing technicians
        self.url = reverse(
            "maintenance_companies:technicians-list", 
            kwargs={"uuid_id": self.maintenance_profile.id},
        )

    def test_list_technicians_success(self):
        """Test listing technicians for a valid maintenance company."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure that both technicians are in the response, regardless of order
        self.assertCountEqual(
            [technician["user"]["email"] for technician in response.data],
            ["tech1@example.com", "tech2@example.com"]
        )

    def test_list_technicians_no_profile(self):
        """Test response when the maintenance company profile does not exist."""
        # Delete the existing maintenance profile
        self.maintenance_profile.delete()

        # Make the request
        response = self.client.get(self.url)

        # Assert 404 status due to the deleted profile
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(str(response.data["detail"]).strip(), "Maintenance company not found")

    def test_list_technicians_invalid_uuid(self):
        """Test error response for a non-existent or invalid maintenance company UUID."""
        invalid_uuid = uuid.uuid4()
        invalid_url = reverse(
            "maintenance_companies:technicians-list", 
            kwargs={"uuid_id": invalid_uuid},
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(str(response.data["detail"]).strip(), "Maintenance company not found")

