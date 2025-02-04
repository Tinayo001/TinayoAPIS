from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from account.models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
import uuid

User = get_user_model()

class TechnicianDetailByEmailViewTests(APITestCase):
    def setUp(self):
        """Set up test data before each test method."""
        self.client = APIClient()
        
        # Create maintenance company
        self.maintenance_user = User.objects.create_user(
            email='maintenance@example.com',
            phone_number='+1234567890',
            password='testpass123',
            first_name='Maintenance',
            last_name='Company',
            account_type='maintenance'
        )
        
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name='Test Maintenance Co',
            company_address='123 Test St',
            registration_number='REG123',
            specialization='HVAC'
        )
        
        # Create technician user
        self.technician_user = User.objects.create_user(
            email='tech@example.com',
            phone_number='+9876543210',
            password='testpass123',
            first_name='John',
            last_name='Doe',
            account_type='technician'
        )
        
        # Create technician profile
        self.technician = TechnicianProfile.objects.create(
            user=self.technician_user,
            specialization='Electrical',
            maintenance_company=self.maintenance_company,
            is_approved=True
        )
        
        # URL for the endpoint
        self.url = reverse('technician-detail-by-email', kwargs={'technician_email': self.technician_user.email})

    def test_get_technician_details_success(self):
        """Test successful retrieval of technician details."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('technician', response.data)
        
        technician_data = response.data['technician']
        self.assertEqual(technician_data['id'], str(self.technician.id))
        self.assertEqual(technician_data['technician_name'], 'John Doe')
        self.assertEqual(technician_data['specialization'], 'Electrical')
        # Convert UUID to string for comparison
        self.assertEqual(str(technician_data['maintenance_company']), str(self.maintenance_company.id))
        self.assertEqual(technician_data['maintenance_company_name'], str(self.maintenance_company))
        self.assertEqual(technician_data['email'], 'tech@example.com')
        self.assertEqual(technician_data['phone_number'], '+9876543210')

    def test_get_technician_invalid_email(self):
        """Test retrieval with invalid email format."""
        url = reverse('technician-detail-by-email', kwargs={'technician_email': 'invalid-email'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Invalid email format.')

    def test_get_technician_nonexistent_email(self):
        """Test retrieval with non-existent email."""
        url = reverse('technician-detail-by-email', kwargs={'technician_email': 'nonexistent@example.com'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'User with this email not found.')

    def test_get_technician_user_without_profile(self):
        """Test retrieval for user without technician profile."""
        # Create user without technician profile
        user_without_profile = User.objects.create_user(
            email='noprofile@example.com',
            phone_number='+1122334455',
            password='testpass123',
            first_name='No',
            last_name='Profile',
            account_type='technician'
        )
        
        url = reverse('technician-detail-by-email', kwargs={'technician_email': user_without_profile.email})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'User has no technician profile associated.')

    def test_technician_without_maintenance_company(self):
        """Test retrieval for technician without maintenance company."""
        # Create technician without maintenance company
        user = User.objects.create_user(
            email='freelance@example.com',
            phone_number='+5544332211',
            password='testpass123',
            first_name='Freelance',
            last_name='Tech',
            account_type='technician'
        )
        
        technician = TechnicianProfile.objects.create(
            user=user,
            specialization='Plumbing',
            maintenance_company=None,
            is_approved=True
        )
        
        url = reverse('technician-detail-by-email', kwargs={'technician_email': user.email})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('technician', response.data)
        technician_data = response.data['technician']
        self.assertIsNone(technician_data['maintenance_company'])
        self.assertIsNone(technician_data['maintenance_company_name'])
