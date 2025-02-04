from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from uuid import uuid4
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from buildings.models import Building
from elevators.models import Elevator
from developers.models import DeveloperProfile  # Assuming you have this model in your project

class UpdateTechnicianOnBuildingsViewTest(TestCase):
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
            email='developer@company.com',
            phone_number='0987654321',
            password='password123',
            first_name='Developer',
            last_name='User',
            account_type='developer'
        )
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.developer_user,
            developer_name="Developer A",
            address="123 Developer St.",
            specialization="Elevators"
        )

        # Create a Technician
        self.technician_user = User.objects.create_user(
            email='technician@company.com',
            phone_number='1122334455',
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

        # Create a Building with a Developer assigned
        self.building = Building.objects.create(
            name="Building One",
            address="123 Building St.",
            contact="contact@building.com",
            developer=self.developer_profile  # Correctly assign the developer
        )

        # Create Elevators
        self.elevator1 = Elevator.objects.create(
            user_name="Elevator 1",
            capacity=1000,
            building=self.building,
            maintenance_company=self.company,
            machine_number="LIFT001",
            manufacturer="ElevatorCorp",
            installation_date="2020-01-01"
        )
        self.elevator2 = Elevator.objects.create(
            user_name="Elevator 2",
            capacity=1200,
            building=self.building,
            maintenance_company=self.company,
            machine_number="LIFT002",
            manufacturer="ElevatorCorp",
            installation_date="2021-01-01"
        )

        # Define the API client
        self.client = APIClient()

    def test_update_technician_success(self):
        """Test assigning a technician to all elevators in a building."""
        url = reverse('maintenance_companies:update-technician-on-buildings', kwargs={
            'company_uuid': str(self.company.id),
            'building_uuid': str(self.building.id)
        })
        
        # Create request data
        data = {
            'technician_id': str(self.technician.id)
        }

        # Send PUT request
        response = self.client.put(url, data, format='json')

        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the elevators are updated with the correct technician
        self.elevator1.refresh_from_db()
        self.elevator2.refresh_from_db()
        self.assertEqual(self.elevator1.technician, self.technician)
        self.assertEqual(self.elevator2.technician, self.technician)

    def test_update_technician_invalid_company(self):
        """Test with an invalid company UUID."""
        invalid_uuid = uuid4()
        url = reverse('maintenance_companies:update-technician-on-buildings', kwargs={
            'company_uuid': str(invalid_uuid),
            'building_uuid': str(self.building.id)
        })
        
        # Create request data
        data = {
            'technician_id': str(self.technician.id)
        }

        # Send PUT request
        response = self.client.put(url, data, format='json')

        # Assert that the company not found error is returned
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Maintenance company not found.', response.data['error'])

    def test_update_technician_missing_technician_id(self):
        """Test when technician_id is missing in the request."""
        url = reverse('maintenance_companies:update-technician-on-buildings', kwargs={
            'company_uuid': str(self.company.id),
            'building_uuid': str(self.building.id)
        })
        
        # Send PUT request without technician_id
        response = self.client.put(url, {}, format='json')

        # Assert that the error is returned for missing technician_id
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Technician ID is required.', response.data['error'])

    def test_update_technician_invalid_technician(self):
        """Test with an invalid technician UUID."""
        invalid_technician_uuid = uuid4()
        url = reverse('maintenance_companies:update-technician-on-buildings', kwargs={
            'company_uuid': str(self.company.id),
            'building_uuid': str(self.building.id)
        })
        
        # Create request data with an invalid technician ID
        data = {
            'technician_id': str(invalid_technician_uuid)
        }

        # Send PUT request
        response = self.client.put(url, data, format='json')

        # Assert that technician not found error is returned
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Technician not found or does not belong to this maintenance company.', response.data['error'])

