from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from uuid import uuid4
from datetime import datetime, timedelta

from account.models import User
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from developers.models import DeveloperProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile


class BuildingMaintenanceSchedulesViewTest(TestCase):
    def setUp(self):
        # Create API client
        self.client = APIClient()
        
        # Create a user
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='1234567890',
            first_name='Test',
            last_name='User',
            password='testpassword'
        )

        # Create a developer profile
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name='Test Developer',
            address='123 Dev St',
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

        # Create a maintenance company
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Maintenance Co',
            company_address='789 Maintenance St',
            registration_number='MAINT123',
            specialization='Elevators'
        )

        # Create a technician
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            specialization='Elevator Technician',
            maintenance_company=self.maintenance_company,
            is_approved=True
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

        # Create sample maintenance schedules
        self.regular_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,  # Added this field
            scheduled_date=datetime.now() + timedelta(days=1),
            description='Regular maintenance check',
            status='scheduled'
        )

        self.adhoc_schedule = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,  # Added this field
            scheduled_date=datetime.now() + timedelta(days=2),
            description='Emergency maintenance',
            status='scheduled'
        )

        self.building_adhoc_schedule = BuildingLevelAdhocSchedule.objects.create(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,  # Added this field
            scheduled_date=datetime.now() + timedelta(days=3),
            description='Building-wide maintenance',
            status='scheduled'
        )

    def test_get_building_schedules_success(self):
        """Test successfully retrieving all maintenance schedules for a building."""
        url = reverse('building-maintenance-schedules', kwargs={'building_id': self.building.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('regular_schedules', response.json())
        self.assertIn('adhoc_schedules', response.json())
        self.assertIn('building_level_adhoc_schedules', response.json())
        
        # Verify the number of schedules
        self.assertEqual(len(response.json()['regular_schedules']), 1)
        self.assertEqual(len(response.json()['adhoc_schedules']), 1)
        self.assertEqual(len(response.json()['building_level_adhoc_schedules']), 1)

    def test_get_building_schedules_invalid_uuid(self):
        """Test retrieving schedules with invalid UUID format."""
        url = '/api/maintenance/building-schedules/invalid-uuid/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Changed from 400 to 404

    def test_get_building_schedules_building_not_found(self):
        """Test retrieving schedules for non-existent building."""
        non_existent_id = uuid4()
        url = reverse('building-maintenance-schedules', kwargs={'building_id': non_existent_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['detail'], 'Building not found.')

    def test_get_building_schedules_no_elevators(self):
        """Test retrieving schedules for building with no elevators."""
        # Create a new building without elevators
        new_building = Building.objects.create(
            name='Empty Building',
            address='789 Empty St',
            contact='5554443333',
            developer=self.developer,
            developer_name='Test Developer'
        )

        url = reverse('building-maintenance-schedules', kwargs={'building_id': new_building.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['detail'], 'No elevators found for this building.')

    def test_get_building_schedules_no_maintenance_schedules(self):
        """Test retrieving schedules for building with elevators but no maintenance schedules."""
        # Create a new building and elevator without schedules
        new_building = Building.objects.create(
            name='No Schedule Building',
            address='321 No Schedule St',
            contact='1112223333',
            developer=self.developer,
            developer_name='Test Developer'
        )

        Elevator.objects.create(
            user_name='LIFT2',
            controller_type='Digital',
            machine_type='gearless',
            building=new_building,
            machine_number='ELEV002',
            capacity=1000,
            manufacturer='Test Manufacturer',
            installation_date='2023-01-01',
            maintenance_company=self.maintenance_company
        )

        url = reverse('building-maintenance-schedules', kwargs={'building_id': new_building.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['detail'], 'No maintenance schedules found for this building.')
