from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from uuid import uuid4
from datetime import datetime, timedelta
from jobs.factories import (
    MaintenanceScheduleFactory, AdHocMaintenanceScheduleFactory,
    BuildingLevelAdhocScheduleFactory, TechnicianProfileFactory,
    DeveloperProfileFactory, ElevatorFactory, BuildingFactory,
    MaintenanceCompanyProfileFactory
)
from jobs.models import (
    MaintenanceSchedule, AdHocMaintenanceSchedule, 
    BuildingLevelAdhocSchedule, Building
)

class MaintenanceScheduleFilterViewTests(TestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.url = '/api/jobs/maintenance-schedules/filter/'
        
        # Create base test data
        self.technician = TechnicianProfileFactory()
        self.developer = DeveloperProfileFactory()
        self.building = BuildingFactory(developer=self.developer)
        self.maintenance_company = MaintenanceCompanyProfileFactory()
        self.elevator = ElevatorFactory(
            building=self.building,
            developer=self.developer,
            maintenance_company=self.maintenance_company
        )
        
        # Create regular maintenance schedule
        self.regular_schedule = MaintenanceScheduleFactory(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            status='scheduled',
            next_schedule='1_month',
            scheduled_date=datetime.now() + timedelta(days=5)  # Add 5 days for scheduled date
        )
        
        # Create ad-hoc maintenance schedule
        self.adhoc_schedule = AdHocMaintenanceScheduleFactory(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            status='scheduled',
            scheduled_date=datetime.now() + timedelta(days=5)
        )
        
        # Create building-level schedule
        self.building_schedule = BuildingLevelAdhocScheduleFactory(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            status='scheduled',
            scheduled_date=datetime.now() + timedelta(days=5)
        )

    def test_filter_by_schedule_type(self):
        """Test filtering by schedule type"""
        # Test regular schedules
        response = self.client.put(
            self.url, 
            {'schedule_type': 'regular'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test adhoc schedules
        response = self.client.put(
            self.url, 
            {'schedule_type': 'adhoc'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test building schedules
        response = self.client.put(
            self.url, 
            {'schedule_type': 'building'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_technician(self):
        """Test filtering by technician"""
        response = self.client.put(
            self.url, 
            {
                'technician_id': str(self.technician.id),
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_status(self):
        """Test filtering by status"""
        response = self.client.put(
            self.url,
            {
                'status': 'scheduled',
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_developer(self):
        """Test filtering by developer"""
        response = self.client.put(
            self.url,
            {
                'developer_id': str(self.developer.id),
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_building(self):
        """Test filtering by building"""
        response = self.client.put(
            self.url,
            {
                'building_id': str(self.building.id),
                'schedule_type': 'building'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_elevator(self):
        """Test filtering by elevator"""
        response = self.client.put(
            self.url,
            {
                'elevator_id': str(self.elevator.id),
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_scheduled_date(self):
        """Test filtering by scheduled date"""
        date = self.regular_schedule.scheduled_date.strftime('%Y-%m-%d')
        response = self.client.put(
            self.url,
            {
                'scheduled_date': date,
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_next_schedule(self):
        """Test filtering by next schedule"""
        response = self.client.put(
            self.url,
            {
                'next_schedule': '1_month',
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_maintenance_company(self):
        """Test filtering by maintenance company"""
        response = self.client.put(
            self.url,
            {
                'maintenance_company_id': str(self.maintenance_company.id),
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_field(self):
        """Test response with invalid field"""
        response = self.client.put(
            self.url,
            {'invalid_field': 'value'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid fields', str(response.data['detail']))

    def test_invalid_uuid(self):
        """Test response with invalid UUID"""
        response = self.client.put(
            self.url,
            {'technician_id': 'invalid-uuid'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid technician ID format', str(response.data['detail']))

    def test_invalid_status(self):
        """Test response with invalid status"""
        response = self.client.put(
            self.url,
            {'status': 'invalid_status'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid status', str(response.data['detail']))

    def test_invalid_next_schedule(self):
        """Test response with invalid next_schedule"""
        response = self.client.put(
            self.url,
            {
                'next_schedule': 'invalid_schedule',
                'schedule_type': 'regular'
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid next_schedule', str(response.data['detail']))

    def test_url_resolves_correctly(self):
        """Test that the URL resolves correctly"""
        url = reverse('maintenance-schedule-filter')
        self.assertEqual(url, '/api/jobs/maintenance-schedules/filter/')

