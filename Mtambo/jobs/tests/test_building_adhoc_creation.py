from datetime import timedelta
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from uuid import uuid4
from django.utils.timezone import now

from buildings.models import Building
from elevators.models import Elevator
from jobs.models import BuildingLevelAdhocSchedule

# Import your factories
from jobs.factories import (
    BuildingFactory,
    ElevatorFactory,
    TechnicianProfileFactory,
    MaintenanceCompanyProfileFactory,
)

class CreateBuildingAdhocScheduleViewTests(APITestCase):
    def setUp(self):
        # Create necessary related objects
        self.maintenance_company = MaintenanceCompanyProfileFactory()
        self.technician = TechnicianProfileFactory(maintenance_company=self.maintenance_company)
        self.building = BuildingFactory()
        
        # Create elevator with all required relationships
        self.elevator = ElevatorFactory(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company
        )
        
        self.url = reverse('building-adhoc-schedule-create', kwargs={'building_id': self.building.id})
        self.valid_data = {'description': 'Urgent maintenance needed'}

    def test_successful_schedule_creation(self):
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(BuildingLevelAdhocSchedule.objects.count(), 1)
        
        schedule = BuildingLevelAdhocSchedule.objects.first()
        self.assertEqual(schedule.building, self.building)
        self.assertEqual(schedule.technician, self.technician)
        self.assertEqual(schedule.maintenance_company, self.maintenance_company)
        self.assertEqual(schedule.description, self.valid_data['description'])
        self.assertEqual(schedule.status, 'scheduled')
        
        # Verify scheduled_date is recent
        self.assertAlmostEqual(
            schedule.scheduled_date,
            now(),
            delta=timedelta(seconds=5)
        )         
    
    def test_building_not_found(self):
        fake_uuid = uuid4()
        url = reverse('building-adhoc-schedule-create', kwargs={'building_id': fake_uuid})
        response = self.client.post(url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(f'Building {fake_uuid} not found', response.data['detail'])

    def test_no_elevators_for_building(self):
        # Delete existing elevator
        Elevator.objects.all().delete()
        
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(f'No elevators found for building {self.building.id}', response.data['detail'])

    def test_missing_technician(self):
        # Create elevator without technician
        self.elevator.technician = None
        self.elevator.save()
        
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(f'Missing technician for elevator {self.elevator.id}', response.data['detail'])

    def test_missing_maintenance_company(self):
        # Create elevator without maintenance company
        self.elevator.maintenance_company = None
        self.elevator.save()
        
        response = self.client.post(self.url, self.valid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn(f'Missing maintenance company for elevator {self.elevator.id}', response.data['detail'])

    def test_invalid_request_data(self):
        response = self.client.post(self.url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('description', response.data)

