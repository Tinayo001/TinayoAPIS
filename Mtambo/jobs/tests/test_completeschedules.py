# jobs/tests/test_completeschedules.py

from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
from buildings.models import Building
from developers.models import DeveloperProfile
from jobs.models import MaintenanceSchedule
from jobs.serializers import MaintenanceScheduleSerializer
from datetime import datetime  # Import datetime

class ChangeMaintenanceScheduleToCompletedViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create a user
        self.user = User.objects.create_user(
            email='technician@example.com',
            phone_number='1234567890',
            password='password',
            first_name='John',
            last_name='Doe',
            account_type='technician'
        )
        
        # Create a maintenance company
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Company',
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
            address='456 Developer St',
            specialization='Elevators'
        )
        
        # Create a building
        self.building = Building.objects.create(
            name='Test Building',
            address='789 Building St',
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
            maintenance_company=self.maintenance_company,
            developer=self.developer,
            technician=self.technician
        )
        
        # Create a maintenance schedule with a datetime object for scheduled_date
        self.maintenance_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            status='scheduled',
            scheduled_date=datetime(2023, 12, 1),  # Use datetime object
            technician=self.technician
        )
        
        # Authenticate the client
        self.client.force_authenticate(user=self.user)

    def test_change_maintenance_schedule_to_completed_success(self):
        url = reverse('complete-maintenance-schedule', args=[self.maintenance_schedule.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'The maintenance schedule has been completed.')
        self.maintenance_schedule.refresh_from_db()
        self.assertEqual(self.maintenance_schedule.status, 'completed')

    def test_change_maintenance_schedule_already_completed(self):
        self.maintenance_schedule.status = 'completed'
        self.maintenance_schedule.save()
        url = reverse('complete-maintenance-schedule', args=[self.maintenance_schedule.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Sorry, this maintenance schedule has already been completed!')

    def test_change_maintenance_schedule_overdue(self):
        self.maintenance_schedule.status = 'overdue'
        self.maintenance_schedule.save()
        url = reverse('complete-maintenance-schedule', args=[self.maintenance_schedule.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'The maintenance schedule was overdue and has now been marked as completed.')
        self.maintenance_schedule.refresh_from_db()
        self.assertEqual(self.maintenance_schedule.status, 'completed')

    def test_change_maintenance_schedule_no_technician(self):
        self.maintenance_schedule.technician = None
        self.maintenance_schedule.save()
        url = reverse('complete-maintenance-schedule', args=[self.maintenance_schedule.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'This maintenance schedule cannot be completed as no technician has been assigned.')

    def test_change_maintenance_schedule_unexpected_status(self):
        self.maintenance_schedule.status = 'unexpected_status'
        self.maintenance_schedule.save()
        url = reverse('complete-maintenance-schedule', args=[self.maintenance_schedule.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unexpected status.')
