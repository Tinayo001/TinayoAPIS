from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
import uuid


class ListPendingTechniciansViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test_maintenance@example.com',
            phone_number='1234567890',
            password='password123',
            first_name='Test',
            last_name='Maintenance',
            account_type='maintenance',
        )
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Maintenance Company',
            company_address='123 Test Address',
            registration_number='REG123',
            specialization='Elevators'
        )
        self.technician = TechnicianProfile.objects.create(
            user=User.objects.create_user(
                email='tech1@example.com',
                phone_number='9876543210',
                password='password123',
                first_name='Tech',
                last_name='One',
                account_type='technician',
            ),
            specialization='Electrical',
            maintenance_company=self.maintenance_company,
            is_approved=False
        )

    def test_list_pending_technicians(self):
        url = reverse('maintenance_companies:list-pending-technicians', kwargs={'company_id': self.maintenance_company.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['pending_technicians'][0]['name'], 'Tech One')

    def test_list_pending_technicians_invalid_company_id(self):
        invalid_company_id = uuid.uuid4()
        url = reverse('maintenance_companies:list-pending-technicians', kwargs={'company_id': invalid_company_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

