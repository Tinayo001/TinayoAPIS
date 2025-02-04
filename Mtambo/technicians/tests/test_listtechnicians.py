from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from uuid import uuid4
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from django.http import QueryDict

class TechnicianListViewTests(APITestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a User instance with the required fields
        cls.user = User.objects.create_user(
            email='user@example.com',
            password='password',
            first_name='Test',
            last_name='User',
            phone_number='1234567890'  # Add the phone_number field here
        )

        # Create a Maintenance company with the correct fields and associate it with the user
        cls.company = MaintenanceCompanyProfile.objects.create(
            user=cls.user,  # Associate the user with the Maintenance company
            company_name='Test Company',
            company_address='123 Test St.',
            registration_number='REG123456',
            specialization='HVAC'
        )
        
        # Create users for technicians
        cls.user1 = User.objects.create_user(
            email='user1@example.com',
            password='password',
            first_name='User',
            last_name='One',
            phone_number='0987654321'  # Add the phone_number field here
        )
        cls.user2 = User.objects.create_user(
            email='user2@example.com',
            password='password',
            first_name='User',
            last_name='Two',
            phone_number='1122334455'  # Add the phone_number field here
        )
        
        # Create technicians and associate them with the company
        cls.technician1 = TechnicianProfile.objects.create(
            user=cls.user1,
            specialization='HVAC',
            maintenance_company=cls.company
        )
        
        cls.technician2 = TechnicianProfile.objects.create(
            user=cls.user2,
            specialization='Elevator',
            maintenance_company=cls.company
        )

    def test_list_all_technicians(self):
        """Test retrieving all technicians without company filter"""
        url = reverse('technician-list-all')  # Correct URL name for listing all technicians
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        technician_ids = [tech['id'] for tech in response.data]
        self.assertIn(str(self.technician1.id), technician_ids)
        self.assertIn(str(self.technician2.id), technician_ids)

    def test_filter_by_company(self):
        """Test retrieving technicians filtered by company UUID"""
        url = reverse('technician-list', kwargs={'company_uuid': str(self.company.id)})  # Correct URL name for filtering by company UUID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        technician_ids = [tech['id'] for tech in response.data]
        self.assertIn(str(self.technician1.id), technician_ids)
        self.assertIn(str(self.technician2.id), technician_ids)

    def test_filter_by_specialization(self):
        """Test retrieving technicians filtered by specialization"""
        url = reverse('technician_list_by_specialization', kwargs={'specialization': 'HVAC'})  # Correct URL name for filtering by specialization
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        technician_ids = [tech['id'] for tech in response.data]
        self.assertIn(str(self.technician1.id), technician_ids)
        self.assertNotIn(str(self.technician2.id), technician_ids)
    
    def test_invalid_company_uuid(self):
        invalid_uuid = '12345678-1234-5678-1234-567812345678'  # Use a valid UUID format but one that doesn't exist
        url = reverse('technician-list', kwargs={'company_uuid': invalid_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Should return empty list for non-existent company 

