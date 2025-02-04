from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from uuid import uuid4
from jobs.models import MaintenanceSchedule, AdHocMaintenanceSchedule, BuildingLevelAdhocSchedule
from elevators.models import Elevator
from buildings.models import Building
from technicians.models import TechnicianProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from account.models import User
from developers.models import DeveloperProfile
from unittest.mock import patch

class MaintenanceScheduleListViewTest(APITestCase):
    def setUp(self):
        # Create users
        self.user_technician = User.objects.create_user(
            email="technician@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="John",
            last_name="Doe",
            account_type="technician"
        )

        # Create technician profile
        self.technician = TechnicianProfile.objects.create(
            user=self.user_technician,
            specialization="Elevator Technician"
        )

        # Create Developer Profile
        self.developer_user = User.objects.create_user(
            email="developer@example.com",
            phone_number="0987654321",
            password="developerpassword",
            first_name="Jane",
            last_name="Doe",
            account_type="developer"
        )

        self.developer_profile = DeveloperProfile.objects.create(
            user=self.developer_user,
            developer_name="Developer A",
            address="123 Developer St",
            specialization="Elevators"
        )

        # Create building
        self.building = Building.objects.create(
            name="Building A",
            address="123 Main St",
            developer=self.developer_profile
        )

        # Create maintenance company
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user_technician,
            company_name="Elevator Repairs Inc.",
            company_address="456 Industry Blvd.",
            registration_number="12345",
            specialization="Elevator Maintenance"
        )

        # Create elevator
        self.elevator = Elevator.objects.create(
            user_name="Elevator 1",
            building=self.building,
            machine_type="gearless",
            machine_number="ELEVATOR001",
            capacity=1000,
            manufacturer="ElevatorCo",
            installation_date="2025-01-01",
            maintenance_company=self.maintenance_company,
            technician=self.technician
        )

        # Create maintenance schedules
        self.schedule_regular = MaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2025-02-01T10:00:00Z",
            next_schedule="1_month",
            description="Regular Maintenance"
        )

        self.schedule_adhoc = AdHocMaintenanceSchedule.objects.create(
            elevator=self.elevator,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2025-02-10T10:00:00Z",
            description="Ad-Hoc Maintenance"
        )

        self.schedule_building_adhoc = BuildingLevelAdhocSchedule.objects.create(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            scheduled_date="2025-02-15T10:00:00Z",
            description="Building-Level Ad-Hoc Maintenance"
        )

    def test_get_all_schedules(self):
        """Test retrieving all maintenance schedules without filters."""
        url = reverse('maintenance-schedule-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('regular_schedules', response.data)
        self.assertIn('adhoc_schedules', response.data)
        self.assertIn('building_level_adhoc_schedules', response.data)
        
        # Verify the number of schedules
        self.assertEqual(len(response.data['regular_schedules']), 1)
        self.assertEqual(len(response.data['adhoc_schedules']), 1)
        self.assertEqual(len(response.data['building_level_adhoc_schedules']), 1)

    def test_filter_by_elevator_id(self):
        """Test retrieving schedules filtered by elevator ID."""
        url = reverse('maintenance-schedule-list') + f"?elevator_id={self.elevator.id}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['regular_schedules']), 1)
        self.assertEqual(len(response.data['adhoc_schedules']), 1)

    def test_filter_by_building_id(self):
        """Test retrieving schedules filtered by building ID."""
        url = reverse('maintenance-schedule-list') + f"?building_id={self.building.id}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['building_level_adhoc_schedules']), 1)

    def test_filter_by_technician_id(self):
        """Test retrieving schedules filtered by technician ID."""
        url = reverse('maintenance-schedule-list') + f"?technician_id={self.technician.id}"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['regular_schedules']), 1)
        self.assertEqual(len(response.data['adhoc_schedules']), 1)
        self.assertEqual(len(response.data['building_level_adhoc_schedules']), 1)

    def test_filter_by_invalid_elevator_id(self):
        """Test retrieving schedules with an invalid elevator ID."""
        url = reverse('maintenance-schedule-list') + "?elevator_id=invalid-uuid"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid elevator_id format. Must be a valid UUID.")

    def test_filter_by_invalid_building_id(self):
        """Test retrieving schedules with an invalid building ID."""
        url = reverse('maintenance-schedule-list') + "?building_id=invalid-uuid"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid building_id format. Must be a valid UUID.")

    def test_filter_by_invalid_technician_id(self):
        """Test retrieving schedules with an invalid technician ID."""
        url = reverse('maintenance-schedule-list') + "?technician_id=invalid-uuid"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid technician_id format. Must be a valid UUID.")

    def test_get_empty_schedule_list(self):
        """Test retrieving schedules when no schedules exist."""
        # Delete all schedules
        MaintenanceSchedule.objects.all().delete()
        AdHocMaintenanceSchedule.objects.all().delete()
        BuildingLevelAdhocSchedule.objects.all().delete()
        
        url = reverse('maintenance-schedule-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['regular_schedules'], [])
        self.assertEqual(response.data['adhoc_schedules'], [])
        self.assertEqual(response.data['building_level_adhoc_schedules'], [])

    def test_server_error_handling(self):
        """Test how the view handles unexpected server errors."""
        url = reverse('maintenance-schedule-list')
        
        with patch('jobs.models.MaintenanceSchedule.objects.all') as mock_queryset:
            mock_queryset.side_effect = Exception("Unexpected error")
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.data['detail'], "An error occurred: Unexpected error")

     
    
