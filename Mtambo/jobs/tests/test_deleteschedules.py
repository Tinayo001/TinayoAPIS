from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.test import force_authenticate
from jobs.views import MaintenanceScheduleDeleteView
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
from buildings.models import Building
from developers.models import DeveloperProfile
import uuid

class MaintenanceScheduleDeleteViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = MaintenanceScheduleDeleteView.as_view()
        self.user = User.objects.create_user(
            email='test@example.com',
            phone_number='1234567890',
            password='testpassword',
            first_name='Test',
            last_name='User'
        )
        
        # Create a DeveloperProfile
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.user,
            developer_name='Test Developer',
            address='123 Test St',
            specialization='Elevators'
        )
        
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Company',
            company_address='123 Test St',
            registration_number='TEST123',
            specialization='Elevators'
        )
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            specialization='Elevators',
            maintenance_company=self.maintenance_company
        )
        
        # Create a Building with the DeveloperProfile
        self.building = Building.objects.create(
            name='Test Building',
            address='123 Test St',
            contact='1234567890',
            developer=self.developer_profile,  # Associate the DeveloperProfile
            developer_name='Test Developer'
        )
        
        self.elevator = Elevator.objects.create(
            user_name='LIFT1',
            controller_type='Digital',
            machine_type='gearless',
            building=self.building,
            machine_number='TEST123',
            capacity=1000,
            manufacturer='Test Manufacturer',
            installation_date='2023-01-01'
        )

    def test_invalid_uuid_format(self):
        request = self.factory.delete('/jobs/maintenance-schedule/delete/invalid-uuid/')
        force_authenticate(request, user=self.user)
        response = self.view(request, schedule_id='invalid-uuid')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"detail": "Invalid UUID format."})

    def test_schedule_not_found(self):
        non_existent_uuid = uuid.uuid4()
        request = self.factory.delete(f'/jobs/maintenance-schedule/delete/{non_existent_uuid}/')
        force_authenticate(request, user=self.user)
        response = self.view(request, schedule_id=non_existent_uuid)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {"detail": "Schedule not found."})

    def test_delete_maintenance_schedule(self):
        maintenance_schedule = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date='2023-12-31T00:00:00Z',
            next_schedule='1_month',
            description='Test Maintenance Schedule',
            status='scheduled'
        )
        request = self.factory.delete(f'/jobs/maintenance-schedule/delete/{maintenance_schedule.id}/')
        force_authenticate(request, user=self.user)
        response = self.view(request, schedule_id=maintenance_schedule.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, {"detail": "Regular maintenance schedule deleted successfully."})
        self.assertFalse(MaintenanceSchedule.objects.filter(id=maintenance_schedule.id).exists())

    def test_delete_ad_hoc_maintenance_schedule(self):
        ad_hoc_schedule = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date='2023-12-31T00:00:00Z',
            description='Test Ad-Hoc Maintenance Schedule',
            status='scheduled'
        )
        request = self.factory.delete(f'/jobs/maintenance-schedule/delete/{ad_hoc_schedule.id}/')
        force_authenticate(request, user=self.user)
        response = self.view(request, schedule_id=ad_hoc_schedule.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, {"detail": "Ad-hoc maintenance schedule deleted successfully."})
        self.assertFalse(AdHocMaintenanceSchedule.objects.filter(id=ad_hoc_schedule.id).exists())

    def test_delete_building_level_adhoc_schedule(self):
        building_level_adhoc_schedule = BuildingLevelAdhocSchedule.objects.create(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date='2023-12-31T00:00:00Z',
            description='Test Building Level Ad-Hoc Schedule',
            status='scheduled'
        )
        request = self.factory.delete(f'/jobs/maintenance-schedule/delete/{building_level_adhoc_schedule.id}/')
        force_authenticate(request, user=self.user)
        response = self.view(request, schedule_id=building_level_adhoc_schedule.id)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, {"detail": "Building-level ad-hoc maintenance schedule deleted successfully."})
        self.assertFalse(BuildingLevelAdhocSchedule.objects.filter(id=building_level_adhoc_schedule.id).exists())
