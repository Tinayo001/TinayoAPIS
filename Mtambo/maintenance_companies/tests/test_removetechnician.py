from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.test import TestCase
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from unittest.mock import patch

class RemoveTechnicianFromCompanyViewTest(TestCase):
    def setUp(self):
        """
        Set up the test environment by creating necessary test data.
        """
        self.client = APIClient()

        # Create maintenance company user
        self.maintenance_user = User.objects.create_user(
            email='maintenance@example.com',
            password='testpass123',
            phone_number='+1234567891',
            first_name='Maintenance',
            last_name='Company',
            account_type='maintenance'
        )

        # Create the MaintenanceCompanyProfile for the maintenance company user
        self.maintenance_profile = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name='Test Company',
            company_address='123 Test Street',
            registration_number='REG123',
            specialization='Elevator Maintenance'
        )

        # Create technician user
        self.user = User.objects.create_user(
            email='technician@example.com',
            password='testpass123',
            phone_number='+1234567890',
            first_name='John',
            last_name='Doe',
            account_type='technician'
        )

        # Create the TechnicianProfile for the technician user and associate with the maintenance company
        self.technician_profile = TechnicianProfile.objects.create(
            user=self.user,
            specialization='Elevator Repair',
            maintenance_company=self.maintenance_profile,
            is_approved=True
        )

        # Authenticate the maintenance company user
        self.client.force_authenticate(user=self.maintenance_user)

        # Generate URL for the API endpoint to remove technician
        self.url = reverse(
            'maintenance_companies:remove_technician_from_company',
            kwargs={
                'maintenance_company_id': self.maintenance_profile.id,
                'technician_id': self.technician_profile.id
            }
        )

    def test_remove_technician_success(self):
        """
        Test case for successful removal of technician from a maintenance company.
        """
        response = self.client.delete(self.url)

        # Refresh technician profile from the database to check the update
        self.technician_profile.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(self.technician_profile.maintenance_company)

    def test_remove_technician_unexpected_error(self):
        """
        Test case for handling unexpected errors (e.g., database errors) during removal.
        """
        # Patch the save method to raise an exception
        with patch.object(TechnicianProfile, 'save', side_effect=Exception('Database error')):
            response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def tearDown(self):
        """
        Clean up the test database by deleting test data.
        """
        User.objects.all().delete()
        MaintenanceCompanyProfile.objects.all().delete()
        TechnicianProfile.objects.all().delete()

