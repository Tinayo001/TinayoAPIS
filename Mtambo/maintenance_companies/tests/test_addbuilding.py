# maintenance_companies/tests/test_update.py
from django.urls import reverse
from rest_framework import status
from django.test import TestCase
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile

class MaintenanceCompanyTestCase(TestCase):
    def setUp(self):
        """
        Set up the test data for maintenance company and user profiles.
        """
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@example.com',
            phone_number='1234567890',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )

        # Create a maintenance company profile
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Maintenance Company',
            company_address='123 Test Street',
            registration_number='TEST123456',
            specialization='HVAC'
        )

        # Define the URL for updating the maintenance company
        self.url = reverse('maintenance_companies:update-maintenance-company', kwargs={'uuid_id': self.maintenance_company.id})

    def test_update_maintenance_company(self):
        """
        Test updating the maintenance company profile using PUT.
        """
        # Define the data for the full update request, including the user field
        data = {
            'user': self.user.id,  # Include the user field, or provide the ID
            'company_name': 'Updated Maintenance Company',
            'company_address': '123 Updated Street',
            'registration_number': 'UPDATED123456',
            'specialization': 'HVAC'
        }

        # Send a PUT request to update the maintenance company
        response = self.client.put(self.url, data, content_type='application/json')

        # Debugging: Print response content to check why it fails
        if response.status_code != status.HTTP_200_OK:
            print("Response Content:", response.content)

        # Refresh the instance from the database
        self.maintenance_company.refresh_from_db()

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.maintenance_company.company_name, 'Updated Maintenance Company')
        self.assertEqual(self.maintenance_company.company_address, '123 Updated Street')
        self.assertEqual(self.maintenance_company.registration_number, 'UPDATED123456')
        self.assertEqual(self.maintenance_company.specialization, 'HVAC')
     

    def test_update_maintenance_company_invalid(self):
        """
        Test updating the maintenance company profile with invalid data.
        """
        data = {
            'company_address': '456 Updated Street',
            'registration_number': 'UPDATED123456',
            'specialization': 'Elevators'
        }

        # Send a PUT request with invalid data (missing company_name)
        response = self.client.put(self.url, data, content_type='application/json')

        # Refresh the instance from the database
        self.maintenance_company.refresh_from_db()

        # Assertions
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.maintenance_company.company_name, 'Test Maintenance Company')  # Should not have changed
        self.assertEqual(self.maintenance_company.company_address, '123 Test Street')
        self.assertEqual(self.maintenance_company.registration_number, 'TEST123456')
        self.assertEqual(self.maintenance_company.specialization, 'HVAC')

