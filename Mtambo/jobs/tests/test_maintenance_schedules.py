from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from uuid import uuid4
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
from buildings.models import Building
from developers.models import DeveloperProfile
from jobs.models import (
    MaintenanceSchedule,
    AdHocMaintenanceSchedule,
    BuildingLevelAdhocSchedule
)

class MaintenanceCompanyMaintenanceSchedulesViewTest(TestCase):
    def setUp(self):
        # Create test client
        self.client = APIClient()
        
        # Create a user
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='1234567890',
            first_name='Test',
            last_name='User',
            password='testpassword'
        )

        # Create a maintenance company
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Maintenance Company',
            company_address='123 Test St',
            registration_number='TEST123',
            specialization='Elevators'
        )

        # Create a technician
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            specialization='Elevator Technician',
            maintenance_company=self.maintenance_company,
            is_approved=True
        )

        # Create a developer
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name='Test Developer',
            address='123 Developer St',
            specialization='Elevators'
        )

        # Create a building
        self.building = Building.objects.create(
            name='Test Building',
            address='456 Test Ave',
            contact='9876543210',
            developer=self.developer,
            developer_name='Test Developer'
        )

        # Create an elevator
        self.elevator = Elevator.objects.create(
            user_name='LIFT1',
            controller_type='Digital',
            machine_type='gearless',
            building=self.building,
            machine_number='ELEV001',
            capacity=1000,
            manufacturer='Test Manufacturer',
            installation_date='2023-01-01',
            maintenance_company=self.maintenance_company
        )

        # Create sample schedules
        self.regular_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date='2023-12-01T10:00:00Z',
            next_schedule='1_month',
            description='Regular maintenance',
            status='scheduled'
        )

        self.adhoc_schedule = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date='2023-12-05T10:00:00Z',
            description='Ad-hoc maintenance',
            status='scheduled'
        )

        self.building_adhoc_schedule = BuildingLevelAdhocSchedule.objects.create(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date='2023-12-10T10:00:00Z',
            description='Building-level ad-hoc maintenance',
            status='scheduled'
        )

    def test_get_maintenance_schedules_success(self):
        """Test successfully retrieving maintenance schedules for a company."""
        url = reverse('maintenance-company-schedules', kwargs={'company_id': self.maintenance_company.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('regular_schedules', response.json())
        self.assertIn('adhoc_schedules', response.json())
        self.assertIn('building_adhoc_schedules', response.json())
        
        # Check that we got the correct number of schedules
        self.assertEqual(len(response.json()['regular_schedules']), 1)
        self.assertEqual(len(response.json()['adhoc_schedules']), 1)
        self.assertEqual(len(response.json()['building_adhoc_schedules']), 1)

    def test_get_maintenance_schedules_company_not_found(self):
        """Test retrieving maintenance schedules for a non-existent company."""
        non_existent_id = uuid4()
        url = reverse('maintenance-company-schedules', kwargs={'company_id': non_existent_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['detail'], 'Maintenance company not found.')

    def test_get_maintenance_schedules_invalid_uuid(self):
        """Test retrieving maintenance schedules with invalid UUID format."""
        url = '/api/jobs/maintenance-schedules/invalid-uuid/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_maintenance_schedules_no_schedules(self):
        """Test retrieving maintenance schedules for a company with no schedules."""
        # Create a new maintenance company with no schedules
        new_user = User.objects.create_user(
            email='new@example.com',
            phone_number='9876543210',
            first_name='New',
            last_name='User',
            password='newpassword'
        )
        
        new_company = MaintenanceCompanyProfile.objects.create(
            user=new_user,
            company_name='New Maintenance Company',
            company_address='789 New St',
            registration_number='NEW123',
            specialization='Elevators'
        )

        url = reverse('maintenance-company-schedules', kwargs={'company_id': new_company.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['detail'], 'No maintenance schedules found for this maintenance company.')
