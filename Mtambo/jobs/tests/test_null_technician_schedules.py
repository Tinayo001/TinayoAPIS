from freezegun import freeze_time
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime, timedelta
import uuid
import pytz  # To make the datetime timezone-aware

from jobs.factories import (
    MaintenanceScheduleFactory,
    DeveloperProfileFactory,
    BuildingFactory,
    MaintenanceCompanyProfileFactory,
    ElevatorFactory,
    TechnicianProfileFactory
)

class MaintenanceScheduleNullTechnicianFilterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create base test data
        self.developer = DeveloperProfileFactory()
        self.maintenance_company = MaintenanceCompanyProfileFactory()
        self.building = BuildingFactory(developer=self.developer)
        self.elevator = ElevatorFactory(
            building=self.building,
            maintenance_company=self.maintenance_company,
            developer=self.developer
        )
        self.technician = TechnicianProfileFactory(
            maintenance_company=self.maintenance_company
        )

        # Create maintenance schedules with and without technicians
        self.schedule_no_tech = MaintenanceScheduleFactory(
            elevator=self.elevator,
            maintenance_company=self.maintenance_company,
            technician=None
        )

        self.schedule_with_tech = MaintenanceScheduleFactory(
            elevator=self.elevator,
            maintenance_company=self.maintenance_company,
            technician=self.technician
        )

        self.url = reverse('unassigned-maintenance-schedules') 

    def test_filter_by_developer(self):
        """Test filtering maintenance schedules by developer ID."""
        data = {'developer_id': str(self.developer.id)}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.schedule_no_tech.id))

    def test_filter_by_invalid_developer(self):
        """Test filtering with non-existent developer ID."""
        data = {'developer_id': str(uuid.uuid4())}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_building(self):
        """Test filtering maintenance schedules by building ID."""
        data = {'building_id': str(self.building.id)}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.schedule_no_tech.id))

    def test_filter_by_invalid_building(self):
        """Test filtering with non-existent building ID."""
        data = {'building_id': str(uuid.uuid4())}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @freeze_time("2024-02-10 12:00:00")  # Freeze time to a known point
    def test_filter_by_scheduled_date(self):
        """Test filtering maintenance schedules by scheduled date."""
        # Create a schedule with today's date
        current_time = datetime.now(pytz.UTC)
        specific_date = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        schedule = MaintenanceScheduleFactory(
            elevator=self.elevator,
            maintenance_company=self.maintenance_company,
            technician=None,
            scheduled_date=specific_date
        )

        MaintenanceScheduleFactory(
            elevator=self.elevator,
            maintenance_company=self.maintenance_company,
            technician=None,
            scheduled_date=specific_date + timedelta(days=1)
        )

        # Format the date as expected by the API
        data = {'scheduled_date': specific_date.strftime('%Y-%m-%d')}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        schedule_ids = [s['id'] for s in response.data]
        self.assertIn(str(schedule.id), schedule_ids)
     
    def test_filter_by_invalid_date_format(self):
        """Test filtering with invalid date format."""
        data = {'scheduled_date': '2024/01/30'}  # Wrong format
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_maintenance_company(self):
        """Test filtering maintenance schedules by maintenance company ID."""
        data = {'maintenance_company_id': str(self.maintenance_company.id)}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.schedule_no_tech.id))

    def test_filter_by_invalid_maintenance_company(self):
        """Test filtering with non-existent maintenance company ID."""
        data = {'maintenance_company_id': str(uuid.uuid4())}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_by_elevator(self):
        """Test filtering maintenance schedules by elevator ID."""
        data = {'elevator_id': str(self.elevator.id)}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.schedule_no_tech.id))

    def test_filter_by_invalid_elevator(self):
        """Test filtering with non-existent elevator ID."""
        data = {'elevator_id': str(uuid.uuid4())}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_multiple_filters(self):
        """Test applying multiple filters simultaneously."""
        data = {
            'developer_id': str(self.developer.id),
            'building_id': str(self.building.id),
            'maintenance_company_id': str(self.maintenance_company.id)
        }
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(self.schedule_no_tech.id))

    def test_invalid_field_name(self):
        """Test request with invalid field name."""
        data = {'invalid_field': 'value'}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid fields', response.data['detail'])

    def test_no_matching_results(self):
        """Test when no maintenance schedules match the filter criteria."""
        # Create a different building and use its ID
        other_building = BuildingFactory()
        data = {'building_id': str(other_building.id)}
        response = self.client.put(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('No non-assigned maintenance schedules found', response.data['detail'])

    def test_empty_request_body(self):
        """Test request with empty body returns all unassigned schedules."""
        response = self.client.put(self.url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
        self.assertTrue(all(s['technician'] is None for s in response.data))

