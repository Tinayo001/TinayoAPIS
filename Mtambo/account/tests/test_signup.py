from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from developers.models import DeveloperProfile

import logging

logger = logging.getLogger(__name__)

class SignUpViewTest(APITestCase):

    def setUp(self):
        self.valid_user_data = {
                'email': 'testuser@example.com',
                'phone_number': '1234567890',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'Password123',
                'account_type': 'developer',
                'developer_name': 'Test Developer',  # Developer-specific field
                'address': '123 Developer St',  # Developer-specific field
                }
        self.valid_maintenance_data = {
                'email': 'maintenance@example.com',
                'phone_number': '1234567890',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'Password123',
                'account_type': 'maintenance',
                'company_name': 'Test Maintenance',
                'company_address': 'Test Street, City',
                'registration_number': '123456',
                'maintenance_company_id': 1,
                'specialization': 'Elevators',
                }

        self.valid_technician_data = {
                'email': 'technician@example.com',
                'phone_number': '1234567890',
                'first_name': 'Test',
                'last_name': 'User',
                'password': 'Password123',
                'account_type': 'technician',
                'specialization': 'Electrical',
                'maintenance_company_id': 1,  # Technician-specific field
                }

        self.invalid_user_data = {
            'email': 'testuser@example.com',
            'phone_number': '',  # Invalid: phone number is blank
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'Password123',
            'account_type': 'developer',
        }

        self.existing_email_data = {
            'email': 'existing@example.com',
            'phone_number': '9876543210',
            'first_name': 'Existing',
            'last_name': 'User',
            'password': 'Password123',
            'account_type': 'maintenance',
        }

        self.invalid_account_type_data = {
            'email': 'invalid@example.com',
            'phone_number': '9876543210',
            'first_name': 'Invalid',
            'last_name': 'User',
            'password': 'Password123',
            'account_type': 'invalid_type',  # Invalid account type
        }
        get_user_model().objects.create_user(
                email='existing@example.com',
                phone_number='9876543210',
                password='Password123',
                first_name='Existing',
                last_name='User',
                account_type='maintenance'
                ) 
 
    def test_signup_successful_developer(self):
        """Test successful signup for Developer account type."""
        data = {
            'email': 'testuser@example.com',
            'phone_number': '1234567890',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'Password123',
            'account_type': 'developer',
            'developer_name': 'Test Developer',
            'address': '123 Developer St'
        }
        response = self.client.post(reverse('signup'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(response.data['account_type'], 'developer')

    def test_signup_successful_maintenance(self):
        """Test successful signup for Maintenance account type."""
        response = self.client.post(reverse('signup'), {
            'email': 'maintenance@example.com',
            'phone_number': '1234567890',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'Password123',
            'account_type': 'maintenance',
            'company_name': 'Test Maintenance',
            'company_address': 'Test Street, City',
            'registration_number': '123456',
            'specialization': 'Elevators'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response content: {response.content}")
        self.assertEqual(response.data['email'], 'maintenance@example.com')
        self.assertEqual(response.data['account_type'], 'maintenance')

        maintenance_profile = MaintenanceCompanyProfile.objects.get(user__email='maintenance@example.com')
        self.assertEqual(maintenance_profile.company_name, 'Test Maintenance')
        self.assertEqual(maintenance_profile.company_address, 'Test Street, City')

    def test_signup_successful_technician(self):
        """Test successful signup for Technician account type."""
        response = self.client.post(reverse('signup'), {
            'email': 'technician@example.com',
            'phone_number': '1234567890',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'Password123',
            'account_type': 'technician',
            'specialization': 'Elevators',
            'maintenance_company_id': 1
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'technician@example.com')
        self.assertEqual(response.data['account_type'], 'technician')

        technician_profile = TechnicianProfile.objects.get(user__email='technician@example.com')
        self.assertEqual(technician_profile.specialization, 'Elevators')

    def test_signup_with_existing_email(self):
        """Test signup failure with an existing email."""
        self.existing_email_data = {
                'name': 'maintenance@example.com',
                'phone_number': '9876543210',
                'first_name': 'Existing',
                'last_name': 'User',
                'password': 'Password123',
                'account_type': 'maintenance',
                }
        response = self.client.post(reverse('signup'), self.existing_email_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_signup_with_invalid_account_type(self):
        """Test signup failure with invalid account type."""
        invalid_data = {
                'email': 'invalid@example.com',
                'phone_number': '9876543210',
                'first_name': 'Invalid',
                'last_name': 'User',
                'password': 'Password123',
                'account_type': 'invalid_type',
                }
        response = self.client.post(reverse('signup'), self.invalid_account_type_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("account_type", response.data)  # Adjusted to check the field

    def test_signup_missing_phone_number(self):
        """Test signup failure when phone number is missing."""
        invalid_data = self.valid_user_data.copy()
        del invalid_data['phone_number']
        response = self.client.post(reverse('signup'), self.invalid_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def test_signup_missing_email(self):
        """Test signup failure when email is missing."""
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = ''
        response = self.client.post(reverse('signup'), invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_signup_missing_password(self):
        """Test signup failure when password is missing."""
        invalid_data = self.valid_user_data.copy()
        invalid_data['password'] = ''
        response = self.client.post(reverse('signup'), invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_signup_missing_required_fields(self):
        """Test signup failure when required fields are missing."""
        invalid_data = self.valid_user_data.copy()
        del invalid_data['phone_number']  # Remove phone number
        response = self.client.post(reverse('signup'), invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone_number", response.data)

    def tearDown(self):
        """Clean up after tests."""
        # Clean up user and profile instances
        DeveloperProfile.objects.filter(user__email='testuser@example.com').delete()
        MaintenanceCompanyProfile.objects.filter(user__email='maintenance@example.com').delete()
        TechnicianProfile.objects.filter(user__email='technician@example.com').delete()
        get_user_model().objects.all().delete()
        
