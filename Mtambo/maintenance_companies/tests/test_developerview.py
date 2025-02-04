from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from uuid import uuid4
from datetime import date
from maintenance_companies.models import MaintenanceCompanyProfile
from developers.models import DeveloperProfile
from account.models import User
from buildings.models import Building
from elevators.models import Elevator

class DevelopersUnderCompanyViewTestCase(TestCase):
    def setUp(self):
        # Create users
        self.user_maintenance = User.objects.create_user(
            email='maintenance@example.com',
            phone_number='1234567890',
            password='password',
            first_name='Maintenance',
            last_name='User',
            account_type='maintenance'
        )
        
        self.user_developer = User.objects.create_user(
            email='developer@example.com',
            phone_number='1112223333',
            password='password',
            first_name='Developer',
            last_name='One',
            account_type='developer'
        )
        
        # Create maintenance company
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.user_maintenance,
            company_name="Test Maintenance Co",
            company_address="123 Test St",
            registration_number="TEST123",
            specialization="Elevators"
        )
        
        # Create developer
        self.developer = DeveloperProfile.objects.create(
            user=self.user_developer,
            developer_name="Test Developer",
            address="456 Dev St",
            specialization="Buildings"
        )
        
        # Create building
        self.building = Building.objects.create(
            name="Test Building",
            address="789 Building St",
            developer=self.developer
        )
        
        # Create elevator with all required fields
        self.elevator = Elevator.objects.create(
            user_name="LIFT1",
            controller_type="Digital",
            machine_type="gearless",
            building=self.building,
            machine_number="TEST-123",  # Unique field
            capacity=1000,
            manufacturer="Test Manufacturer",
            installation_date=date(2024, 1, 15),
            maintenance_company=self.company,
            developer=self.developer
        )

    def test_get_developers_for_valid_company(self):
        """Test getting developers for a valid maintenance company"""
        url = reverse('maintenance_companies:developers-under-company', kwargs={'company_id': str(self.company.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['developer_name'], self.developer.developer_name)

    def test_get_developers_for_nonexistent_company(self):
        """Test getting developers for a non-existent company"""
        non_existent_id = uuid4()
        url = reverse('maintenance_companies:developers-under-company', kwargs={'company_id': str(non_existent_id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], f"Maintenance company with id {non_existent_id} not found.")

    def test_get_developers_no_developers_found(self):
        """Test when no developers are found for a company"""
        # Create new company with no linked buildings/developers
        new_company = MaintenanceCompanyProfile.objects.create(
            user=User.objects.create_user(
                email='another@example.com',
                phone_number='9999999999',
                password='password',
                account_type='maintenance'
            ),
            company_name="No Developers Co",
            company_address="999 Empty St",
            registration_number="EMPTY123",
            specialization="Elevators"
        )
        
        url = reverse('maintenance_companies:developers-under-company', kwargs={'company_id': str(new_company.id)})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "No developers found under this maintenance company.")

    def tearDown(self):
        """Clean up created objects"""
        User.objects.all().delete()
        MaintenanceCompanyProfile.objects.all().delete()
        DeveloperProfile.objects.all().delete()
        Building.objects.all().delete()
        Elevator.objects.all().delete()
