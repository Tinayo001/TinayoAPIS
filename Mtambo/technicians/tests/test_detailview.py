from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from account.models import User
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
import uuid

class TechnicianDetailViewTests(APITestCase):

    def setUp(self):
        # Create a maintenance company user
        self.maintenance_user = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="Maintenance",
            last_name="Company",
            account_type="maintenance"
        )
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name="Test Maintenance Co.",
            company_address="123 Test Lane",
            registration_number="REG123456",
            specialization="HVAC"
        )

        # Create a technician user
        self.technician_user = User.objects.create_user(
            email="technician@example.com",
            phone_number="0987654321",
            password="password123",
            first_name="Tech",
            last_name="Nician",
            account_type="technician"
        )
        self.technician = TechnicianProfile.objects.create(
            user=self.technician_user,
            specialization="HVAC",
            maintenance_company=self.maintenance_company,
            is_approved=True
        )

        # URL for technician detail view
        self.detail_url = reverse('technician-detail', kwargs={'id': str(self.technician.id)})
    
    def test_get_valid_technician(self):
        """Test retrieving details of a valid technician"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['technician_name'], "Tech Nician")
        self.assertEqual(response.data['specialization'], "HVAC")
        self.assertEqual(response.data['maintenance_company_name'], "Test Maintenance Co.")
        self.assertEqual(response.data['email'], "technician@example.com")
        self.assertEqual(response.data['phone_number'], "0987654321")

    def test_get_invalid_technician(self):
        """Test retrieving details of a technician that doesn't exist"""
        invalid_url = reverse('technician-detail', kwargs={'id': str(uuid.uuid4())})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_structure(self):
        """Test the overall response structure"""
        response = self.client.get(self.detail_url)
        expected_fields = ['id', 'technician_name', 'specialization', 'maintenance_company_name', 'email', 'phone_number']
        self.assertTrue(all(field in response.data for field in expected_fields))


