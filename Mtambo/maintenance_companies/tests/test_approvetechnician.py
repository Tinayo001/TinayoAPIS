from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from account.models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
import uuid

class CompanyAddTechnicianViewTests(APITestCase):
    def setUp(self):
        """Set up test data for maintenance company, technician, and user profiles."""
        # Create a maintenance user and profile
        self.maintenance_user = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password",
            first_name="John",
            last_name="Doe",
            account_type="maintenance",  # Assuming 'maintenance' is a valid account_type
        )
        self.maintenance_profile = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name="Test Maintenance Co",
            company_address="123 Main St",
            registration_number="REG123",
            specialization="Elevators",
        )

        # Create a technician user and profile
        self.technician_user = User.objects.create_user(
            email="technician@example.com",
            phone_number="0987654321",
            password="password",
            first_name="Jane",
            last_name="Smith",
            account_type="technician",  # Assuming 'technician' is a valid account_type
        )
        self.technician_profile = TechnicianProfile.objects.create(
            user=self.technician_user,
            specialization="HVAC",
            maintenance_company=self.maintenance_profile,
            is_approved=False,
        )

        # Create API client and define the URL for the test
        self.client = APIClient()
        self.url = reverse('maintenance_companies:company-add-technician', kwargs={'technician_id': self.technician_profile.id})

    def test_approve_pending_technician(self):
        """Test approving a pending technician."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh the technician profile from the database
        self.technician_profile.refresh_from_db()

        # Assert that the technician is now approved
        self.assertTrue(self.technician_profile.is_approved)

        # Assert that the response contains the technician data
        self.assertIn("technician", response.data)
        self.assertEqual(response.data["technician"]["id"], str(self.technician_profile.id))

    def test_approve_already_approved_technician(self):
        """Test trying to approve a technician who is already approved."""
        self.technician_profile.is_approved = True
        self.technician_profile.save()

        response = self.client.post(self.url)

        # Ensure the response indicates an error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Technician is already approved")

    def test_approve_nonexistent_technician(self):
        """Test approving a technician with an invalid ID."""
        invalid_url = reverse('maintenance_companies:company-add-technician', kwargs={'technician_id': uuid.uuid4()})
        response = self.client.post(invalid_url)

        # Ensure the response indicates that the technician was not found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["error"], "Technician not found")

