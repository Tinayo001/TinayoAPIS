import uuid
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.utils import timezone
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from buildings.models import Building
from elevators.models import Elevator
from account.models import User
from developers.models import DeveloperProfile


class CreateRoutineMaintenanceScheduleViewTest(APITestCase):
    def setUp(self):
        """
        Setup test data: Create a user, developer profile, building, elevator, maintenance company, technician.
        """
        self.user = User.objects.create_user(
            email="testuser@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="123 Developer St",
            specialization="Elevators"
        )
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name="Test Maintenance Company",
            company_address="123 Maintenance St",
            registration_number="TMC123",
            specialization="Elevators"
        )
        self.technician_profile = TechnicianProfile.objects.create(
            user=self.user,
            specialization="Elevator Maintenance",
            maintenance_company=self.maintenance_company,
            is_approved=True
        )
        self.building = Building.objects.create(
            name="Test Building",
            address="123 Building St",
            contact="contact@building.com",
            developer_name="Test Developer",
            developer=self.developer_profile
        )
        self.elevator = Elevator.objects.create(
            user_name="Lift1",
            building=self.building,
            machine_number="LIFT001",
            capacity=1000,
            manufacturer="Elevator Inc.",
            installation_date=timezone.now().date(),
            maintenance_company=self.maintenance_company,
            technician=self.technician_profile
        )
        self.url = reverse('create-maintenance-schedule', args=[str(self.elevator.id)])

    def test_create_maintenance_schedule_success(self):
        """
        Test creating a maintenance schedule successfully for an elevator.
        """
        data = {
            "next_schedule": "3_months",
            "scheduled_date": "2025-04-15",
            "description": "Routine maintenance for Lift1"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], "Maintenance schedule created successfully")
        self.assertIn('maintenance_schedule_id', response.data)
        maintenance_schedule_id = str(response.data['maintenance_schedule_id'])
        self.assertTrue(isinstance(maintenance_schedule_id, str))
        try:
            uuid.UUID(maintenance_schedule_id)
        except ValueError:
            self.fail("maintenance_schedule_id is not a valid UUID")

    def test_create_maintenance_schedule_invalid_uuid(self):
        """
        Test creating a maintenance schedule with an invalid elevator UUID format.
        """
        invalid_uuid = "not-a-uuid"
        url = f"/api/jobs/elevators/{invalid_uuid}/maintenance-schedules/"
        data = {
            "next_schedule": "3_months",
            "scheduled_date": "2025-04-15",
            "description": "Routine maintenance for a non-existing lift"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_maintenance_schedule_invalid_date(self):
        """
        Test creating a maintenance schedule with an invalid scheduled_date format.
        """
        data = {
            "next_schedule": "3_months",
            "scheduled_date": "15-04-2025",  # Invalid format
            "description": "Routine maintenance for Lift1"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        expected_error = "Invalid date format. Please provide a valid date in the format 'YYYY-MM-DD' or 'YYYY-MM-DDTHH:MM:SSZ'."
        self.assertEqual(str(response.data['detail']), expected_error)

    def test_create_maintenance_schedule_date_in_past(self):
        """
        Test creating a maintenance schedule with a date in the past.
        """
        data = {
            "next_schedule": "3_months",
            "scheduled_date": "2023-04-15",  # Past date
            "description": "Routine maintenance for Lift1"
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], "Scheduled date cannot be in the past.") 
