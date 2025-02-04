from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from maintenance_companies.models import MaintenanceCompanyProfile
from account.models import User
import uuid

class MaintenanceCompanyListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        Set up test data for all test methods.
        """
        cls.client = APIClient()

        # Create User instances
        cls.user1 = User.objects.create_user(
            email="user1@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="User",
            last_name="One",
        )
        cls.user2 = User.objects.create_user(
            email="user2@example.com",
            phone_number="0987654321",
            password="password123",
            first_name="User",
            last_name="Two",
        )

        # Create MaintenanceCompanyProfile instances
        cls.profile1 = MaintenanceCompanyProfile.objects.create(
            user=cls.user1,
            company_name="Company 1",
            company_address="123 Test St",
            registration_number="REG001",
            specialization="Elevators",
        )
        cls.profile2 = MaintenanceCompanyProfile.objects.create(
            user=cls.user2,
            company_name="Company 2",
            company_address="456 Test Ave",
            registration_number="REG002",
            specialization="HVAC",
        )

        # Define API URL
        cls.url = reverse('maintenance_companies:maintenance_company_list')

    def test_list_maintenance_companies_status_code(self):
        """
        Test that the API endpoint returns a 200 OK status code.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_maintenance_companies_data(self):
        """
        Test that the API endpoint returns the correct data.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Validate the response data
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['company_name'], "Company 1")
        self.assertEqual(data[1]['company_name'], "Company 2")

    def test_maintenance_company_profile_str_method(self):
        """
        Test the string representation of MaintenanceCompanyProfile.
        """
        self.assertEqual(str(self.profile1), "Company 1")
        self.assertEqual(str(self.profile2), "Company 2")

    def test_maintenance_company_profile_fields(self):
        """
        Test the fields of the MaintenanceCompanyProfile model.
        """
        profile = MaintenanceCompanyProfile.objects.get(company_name="Company 1")

        self.assertEqual(profile.company_address, "123 Test St")
        self.assertEqual(profile.registration_number, "REG001")
        self.assertEqual(profile.specialization, "Elevators")
        self.assertIsInstance(profile.id, uuid.UUID)  # Check UUID

    def test_maintenance_model_str_method(self):
        """
        Test the string representation of the Maintenance model.
        """
        self.assertEqual(str(self.profile1), "Company 1")
        self.assertEqual(str(self.profile2), "Company 2")

    def test_invalid_url(self):
        """
        Test that an invalid URL returns a 404 status.
        """
        invalid_url = '/invalid-url/'
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

