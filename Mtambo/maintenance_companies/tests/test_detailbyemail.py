from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile


class MaintenanceCompanyByEmailViewTests(APITestCase):
    def setUp(self):
        # Create a maintenance user with a profile
        self.maintenance_user = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="John",
            last_name="Doe",
            account_type="maintenance"  # Correct usage of AccountType
        )
        self.maintenance_profile = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name="Test Maintenance Co",
            company_address="123 Test St",
            registration_number="REG123",
            specialization="HVAC"
        )

        # Create a regular user without a maintenance profile
        self.regular_user = User.objects.create_user(
            email="regular@example.com",
            phone_number="0987654321",
            password="password123",
            first_name="Jane",
            last_name="Smith",
            account_type="developer"  # Correct usage of AccountType
        )

        # Create a maintenance user without a profile
        self.user_no_profile = User.objects.create_user(
            email="no-profile@example.com",
            phone_number="1122334455",
            password="password123",
            first_name="Alice",
            last_name="Johnson",
            account_type="maintenance"  # Correct usage of AccountType
        )

    def test_retrieve_maintenance_company_by_email_success(self):
        """Ensure maintenance company details are retrieved for a valid email."""
        url = reverse('maintenance_companies:maintenance-company-by-email', kwargs={'email': self.maintenance_user.email})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], "Test Maintenance Co")
        self.assertEqual(response.data['specialization'], "HVAC")

    def test_retrieve_maintenance_company_by_email_not_found(self):
        """Ensure 404 is returned for a non-existent user."""
        url = reverse('maintenance_companies:maintenance-company-by-email', kwargs={'email': 'nonexistent@example.com'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "User with this email not found.")

    def test_retrieve_maintenance_company_by_email_no_profile(self):
        """Ensure 404 is returned for a user with no associated maintenance profile."""
        url = reverse('maintenance_companies:maintenance-company-by-email', kwargs={'email': self.user_no_profile.email})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "User has no maintenance company associated.")

    def test_invalid_email_format(self):
        """Ensure 404 is returned for an invalid email format."""
        url = reverse('maintenance_companies:maintenance-company-by-email', kwargs={'email': 'invalid-email'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "User with this email not found.")  # Update as per your validation logic

