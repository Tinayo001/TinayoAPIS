from django.test import TestCase
from django.urls import reverse
from account.models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
import uuid

class MaintenanceCompanyProfileTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a Maintenance user
        cls.maintenance_user = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="Maintenance",
            last_name="User",
            account_type="maintenance"
        )

        # Create a MaintenanceCompanyProfile
        cls.maintenance_profile = MaintenanceCompanyProfile.objects.create(
            user=cls.maintenance_user,
            company_name="Test Maintenance Company",
            company_address="123 Test Street",
            registration_number="12345",
            specialization="Elevators"
        )

    def test_maintenance_company_profile_creation(self):
        self.assertEqual(MaintenanceCompanyProfile.objects.count(), 1)
        self.assertEqual(self.maintenance_profile.company_name, "Test Maintenance Company")
        self.assertEqual(self.maintenance_profile.company_address, "123 Test Street")

    def test_string_representation(self):
        self.assertEqual(str(self.maintenance_profile), "Test Maintenance Company")


class TechnicianTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a Technician user
        cls.technician_user = User.objects.create_user(
            email="technician@example.com",
            phone_number="0987654321",
            password="password123",
            first_name="Technician",
            last_name="User",
            account_type="technician"
        )

        # Create a TechnicianProfile
        cls.technician_profile = TechnicianProfile.objects.create(
            user=cls.technician_user,
            specialization="HVAC",
            maintenance_company=None,  # No company initially
            is_approved=False
        )

    def test_technician_creation(self):
        self.assertEqual(TechnicianProfile.objects.count(), 1)
        self.assertEqual(self.technician_profile.specialization, "HVAC")
        self.assertFalse(self.technician_profile.is_approved)

    def test_string_representation(self):
        self.assertEqual(str(self.technician_profile), "Technician User - Unlinked")


class MaintenanceCompanyProfileViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a Maintenance user and profile
        cls.maintenance_user = User.objects.create_user(
            email="maintenance_view@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="Maintenance",
            last_name="ViewUser",
            account_type="maintenance"
        )

        cls.maintenance_profile = MaintenanceCompanyProfile.objects.create(
            user=cls.maintenance_user,
            company_name="View Test Maintenance Company",
            company_address="456 Test Avenue",
            registration_number="67890",
            specialization="Generators"
        )

    def test_maintenance_company_list_view(self):
        url = reverse('maintenance_companies:maintenance_company_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Test Maintenance Company")

    def test_maintenance_company_detail_view(self):
        url = reverse('maintenance_companies:maintenance-company-detail', kwargs={'uuid_id': self.maintenance_profile.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "View Test Maintenance Company")

    def test_maintenance_company_detail_view_invalid_uuid(self):
        # Generate a valid UUID that does not exist in the database
        invalid_uuid = uuid.uuid4()
        url = reverse('maintenance_companies:maintenance-company-detail', kwargs={'uuid_id': invalid_uuid})

        # Send a GET request to the endpoint
        response = self.client.get(url)

        # Assert that the status code is 404 (Not Found)
        self.assertEqual(response.status_code, 404)
        # Assert that the response contains the expected message
        self.assertContains(response, "Company not found", status_code=404)

