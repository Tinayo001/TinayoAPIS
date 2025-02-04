from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from uuid import uuid4
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
from buildings.models import Building
from developers.models import DeveloperProfile

class UpdateTechnicianOnElevatorViewTest(TestCase):
    def setUp(self):
        """Setup test data."""
        # Create a Maintenance Company
        self.company_user = User.objects.create_user(
            email='maintenance@company.com',
            phone_number='1234567890',
            password='password123',
            first_name='Maintenance',
            last_name='User',
            account_type='maintenance'
        )
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.company_user,
            company_name='Maintenance Co.',
            company_address='123 Maintenance St.',
            registration_number='ABC123',
            specialization='Elevators'
        )

        # Create a Developer
        self.developer_user = User.objects.create_user(
            email='developer@test.com',
            phone_number='1122334455',
            password='password123',
            first_name='Developer',
            last_name='User',
            account_type='developer'
        )
        self.developer = DeveloperProfile.objects.create(
            user=self.developer_user,
            developer_name='Developer Company',
            address='123 Developer St.',
            specialization='Elevators'
        )

        # Create a Technician
        self.technician_user = User.objects.create_user(
            email='technician@company.com',
            phone_number='0987654321',
            password='password123',
            first_name='John',
            last_name='Doe',
            account_type='technician'
        )
        self.technician = TechnicianProfile.objects.create(
            user=self.technician_user,
            specialization='Elevator Repair',
            maintenance_company=self.company
        )

        # Create a Building with Developer
        self.building = Building.objects.create(
            name="Building One",
            address="123 Building St.",
            contact="contact@building.com",
            developer_name=self.developer.developer_name,
            developer=self.developer
        )

        # Create an Elevator
        self.elevator = Elevator.objects.create(
            user_name="Elevator 1",
            capacity=1000,
            building=self.building,
            maintenance_company=self.company,
            machine_number="LIFT001",
            manufacturer="ElevatorCorp",
            installation_date="2020-01-01"
        )

        # Define the API client
        self.client = APIClient()

    def test_update_technician_success(self):
        """Test assigning a technician to an elevator successfully."""
        url = reverse('maintenance_companies:update-technician-on-elevator', kwargs={
            'company_uuid': str(self.company.id),
            'elevator_uuid': str(self.elevator.id)
        })
        
        data = {
            'technician_id': str(self.technician.id)
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.elevator.refresh_from_db()
        self.assertEqual(self.elevator.technician, self.technician)

    def test_update_technician_missing_technician_id(self):
        """Test when technician_id is missing in the request."""
        url = reverse('maintenance_companies:update-technician-on-elevator', kwargs={
            'company_uuid': str(self.company.id),
            'elevator_uuid': str(self.elevator.id)
        })
        
        response = self.client.put(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Technician ID is required.')

    def test_update_technician_invalid_company(self):
        """Test with an invalid company UUID."""
        invalid_uuid = uuid4()
        url = reverse('maintenance_companies:update-technician-on-elevator', kwargs={
            'company_uuid': str(invalid_uuid),
            'elevator_uuid': str(self.elevator.id)
        })
    
        data = {
            'technician_id': str(self.technician.id)
        }

        response = self.client.put(url, data, format='json')

        # Check if the error message starts with the expected string
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.data['detail'].startswith('No MaintenanceCompany'))
    
    def test_update_technician_invalid_elevator(self):
        """Test with an invalid elevator UUID."""
        invalid_elevator_uuid = uuid4()
        url = reverse('maintenance_companies:update-technician-on-elevator', kwargs={
            'company_uuid': str(self.company.id),
            'elevator_uuid': str(invalid_elevator_uuid)
        })
    
        data = {
            'technician_id': str(self.technician.id)
        }

        response = self.client.put(url, data, format='json')

        # Updated to check the actual error message for invalid elevator
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No Elevator matches the given query.')
     

    def test_update_technician_invalid_technician(self):
        """Test with an invalid technician UUID."""
        invalid_technician_uuid = uuid4()
        url = reverse('maintenance_companies:update-technician-on-elevator', kwargs={
            'company_uuid': str(self.company.id),
            'elevator_uuid': str(self.elevator.id)
        })
    
        data = {
            'technician_id': str(invalid_technician_uuid)
        }

        response = self.client.put(url, data, format='json')

        # Updated to check the actual error message for invalid technician
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No TechnicianProfile matches the given query.')
     
