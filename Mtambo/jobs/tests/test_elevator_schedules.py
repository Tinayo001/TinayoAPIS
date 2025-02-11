from django.test import TestCase, RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from uuid import uuid4
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from buildings.models import Building
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile

from developers.models import DeveloperProfile  # Ensure this import is present

from django.utils import timezone
from datetime import datetime

class ElevatorMaintenanceSchedulesViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.factory = RequestFactory()

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
            address='123 Developer St',
            specialization='Elevators'
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

        # Create a building and associate it with the developer
        self.building = Building.objects.create(
            name='Test Building',
            address='456 Test Ave',
            contact='9876543210',
            developer=self.developer,  # Associate the building with the developer
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

        # Create timezone-aware datetime for maintenance schedules
        scheduled_date_1 = timezone.make_aware(datetime.strptime('2023-12-01T10:00:00', '%Y-%m-%dT%H:%M:%S'))
        scheduled_date_2 = timezone.make_aware(datetime.strptime('2023-12-05T10:00:00', '%Y-%m-%dT%H:%M:%S'))
        scheduled_date_3 = timezone.make_aware(datetime.strptime('2023-12-10T10:00:00', '%Y-%m-%dT%H:%M:%S'))

        # Create a regular maintenance schedule
        self.regular_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date=scheduled_date_1,
            next_schedule='1_month',
            description='Regular maintenance',
            status='scheduled'
        )

        # Create an ad-hoc maintenance schedule
        self.adhoc_schedule = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date=scheduled_date_2,
            description='Ad-hoc maintenance',
            status='scheduled'
        )

        # Create a building-level ad-hoc schedule
        self.building_adhoc_schedule = BuildingLevelAdhocSchedule.objects.create(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date=scheduled_date_3,
            description='Building-level ad-hoc maintenance',
            status='scheduled'
        )
    
    def test_get_maintenance_schedules_for_elevator_with_schedules(self):
        """
        Test retrieving maintenance schedules for an elevator that has schedules.
        """
        url = reverse('elevator-maintenance-schedules', kwargs={'elevator_id': self.elevator.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('regular_schedules', response.data)
        self.assertIn('adhoc_schedules', response.data)
        self.assertIn('building_adhoc_schedules', response.data)

        self.assertEqual(len(response.data['regular_schedules']), 1)
        self.assertEqual(len(response.data['adhoc_schedules']), 1)
        self.assertEqual(len(response.data['building_adhoc_schedules']), 1)

    def test_get_maintenance_schedules_for_elevator_without_schedules(self):
        """
        Test retrieving maintenance schedules for an elevator that has no schedules.
        """
        # Create a new building without any schedules
        building_without_schedules = Building.objects.create(
            name='Test Building Without Schedules',
            address='789 No Schedule Ave',
            contact='5555555555',
            developer=self.developer,
            developer_name='Test Developer'
        )

        # Create another elevator without any schedules, using the new building
        elevator_without_schedules = Elevator.objects.create(
            user_name='LIFT2',
            controller_type='Analog',
            machine_type='geared',
            building=building_without_schedules,  # Use the new building instead of self.building
            machine_number='ELEV002',
            capacity=800,
            manufacturer='Test Manufacturer',
            installation_date='2023-02-01',
            maintenance_company=self.maintenance_company
        )

    def test_get_maintenance_schedules_for_nonexistent_elevator(self):
        """
        Test retrieving maintenance schedules for an elevator that does not exist.
        """
        non_existent_elevator_id = uuid4()
        url = reverse('elevator-maintenance-schedules', kwargs={'elevator_id': non_existent_elevator_id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

