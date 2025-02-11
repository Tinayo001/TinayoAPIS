import uuid
from django.test import TestCase
from rest_framework import status
from django.urls import reverse
from maintenance_companies.models import MaintenanceCompanyProfile
from elevators.models import Elevator
from account.models import User
from django.utils import timezone
from buildings.models import Building
from developers.models import DeveloperProfile

class ElevatorDetailByMachineNumberViewTest(TestCase):
    """
    Test suite for the ElevatorDetailByMachineNumberView.
    """

    def setUp(self):
        """
        Set up the test environment.
        Create a maintenance company, user, building, and an elevator instance.
        """
        # Create a test user
        self.test_user = User.objects.create_user(
            email="testuser@example.com",
            phone_number="123456789",
            password="password123",
            first_name="Test",
            last_name="User",
            account_type="maintenance"
        )

        # Create a maintenance company profile
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.test_user,
            company_name="Test Maintenance Co.",
            company_address="123 Test Street",
            registration_number="TEST1234"
        )

        # Create a developer profile
        self.developer = DeveloperProfile.objects.create(
            developer_name="Test Developer",
            address="123 Developer St.",
            specialization="Elevators"
        )

        # Create a building instance
        self.building = Building.objects.create(
            name="Test Building",
            address="123 Building St.",
            contact="123-456-789",
            developer=self.developer
        )

        # Create an elevator with an alphanumeric machine number
        self.elevator = Elevator.objects.create(
            user_name="Elevator 1",
            machine_type="gearless",
            building=self.building,
            machine_number="ELEV-123A",
            capacity=10,
            manufacturer="Hawaii",
            installation_date=timezone.now().date(),
            maintenance_company=self.company
        )

        # Base URL for the elevator details API view
        self.base_url = '/api/maintenance-companies/elevators'

    def test_get_elevator_details_valid(self):
        """Test a valid GET request for elevator details."""
        url = reverse('maintenance_companies:elevator-detail-by-machine-number',
                     kwargs={
                         'company_id': str(self.company.id),
                         'machine_number': self.elevator.machine_number
                     })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['machine_number'], self.elevator.machine_number)
        self.assertEqual(response.data['user_name'], self.elevator.user_name)
        self.assertEqual(response.data['manufacturer'], self.elevator.manufacturer)

    def test_get_elevator_details_invalid_machine_number(self):
        """Test GET request with an invalid machine number."""
        url = reverse('maintenance_companies:elevator-detail-by-machine-number',
                     kwargs={
                         'company_id': str(self.company.id),
                         'machine_number': 'UNKNOWN123'
                     })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Elevator with the specified machine number not found', str(response.data))

    def test_get_elevator_details_invalid_company(self):
        """Test GET request with an invalid but correctly formatted company ID."""
        invalid_company_id = uuid.uuid4()
        url = reverse('maintenance_companies:elevator-detail-by-machine-number',
                     kwargs={
                         'company_id': str(invalid_company_id),
                         'machine_number': self.elevator.machine_number
                     })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Maintenance company profile not found', str(response.data))

    def test_get_elevator_details_empty_machine_number(self):
        """Test GET request with empty machine number."""
        url = reverse('maintenance_companies:elevator-detail-by-machine-number',
                    kwargs={
                        'company_id': str(self.company.id),
                        'machine_number': ' '
                    })
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Machine number is required', str(response.data)) 
    
    def test_get_elevator_details_invalid_uuid_format(self):
        """Test GET request with invalid UUID format."""
        url = f'{self.base_url}/invalid-uuid/ELEV-123A/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_elevator_details_alphanumeric_machine_number(self):
        """Test GET request with an alphanumeric machine number."""
        url = reverse('maintenance_companies:elevator-detail-by-machine-number',
                     kwargs={
                         'company_id': str(self.company.id),
                         'machine_number': 'ELEV-123A'
                     })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['machine_number'], 'ELEV-123A')

    def test_get_elevator_details_invalid_machine_number_format(self):
        """Test GET request with a machine number containing special characters."""
        url = reverse('maintenance_companies:elevator-detail-by-machine-number',
                     kwargs={
                         'company_id': str(self.company.id),
                         'machine_number': 'INVALID@#$%'
                     })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Machine number must be alphanumeric', str(response.data))

