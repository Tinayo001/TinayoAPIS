from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from uuid import uuid4
from django.contrib.auth import get_user_model
from maintenance_companies.models import MaintenanceCompanyProfile
from buildings.models import Building
from elevators.models import Elevator
from technicians.models import TechnicianProfile
from developers.models import DeveloperProfile

User = get_user_model()

class AddElevatorToBuildingViewTest(APITestCase):
    def setUp(self):
        # Create a user (maintenance type)
        self.user = User.objects.create_user(
            email='maintenance@example.com',
            phone_number='1234567890',
            password='password123',
            first_name='John',
            last_name='Doe',
            account_type='maintenance'
        )
        self.client.login(email='maintenance@example.com', password='password123')

        # Create a maintenance company
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Elevator Maintenance Ltd',
            company_address='123 Elevator St',
            registration_number='ELEV12345'
        )

        # Create a developer and building
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Developer A",
            address="123 Developer St",
            specialization="Elevators"
        )

        # Create the building
        self.building = Building.objects.create(
            name='Building A',
            address='123 Main St',
            contact='555-1234',
            developer=self.developer,
            developer_name="Developer A"
        )

        # Create a technician
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            specialization="Elevator Technician",
            maintenance_company=self.company,
            is_approved=True
        )

    def test_add_elevator_to_building(self):
        url = reverse('maintenance_companies:add_elevator_to_building', 
                    kwargs={'company_uuid': self.company.id, 'building_uuid': self.building.id})

        data = {
            'user_name': 'LIFT1',
            'controller_type': 'Digital',
            'machine_type': 'gearless',
            'machine_number': 'LIFT001',
            'capacity': 1000,
            'manufacturer': 'Elevator Co.',
            'installation_date': '2025-01-01',
            'technician': str(self.technician.id),
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['user_name'], 'LIFT1')
        self.assertEqual(response.data['machine_number'], 'LIFT001')
        self.assertEqual(response.data['capacity'], 1000)
        self.assertEqual(response.data['manufacturer'], 'Elevator Co.')
        self.assertEqual(response.data['installation_date'], '2025-01-01')
        self.assertEqual(response.data['technician'], str(self.technician.id))

    def test_add_elevator_invalid_data(self):
        url = reverse('maintenance_companies:add_elevator_to_building', 
                    kwargs={'company_uuid': self.company.id, 'building_uuid': self.building.id})

        data = {
            'user_name': 'LIFT1',
            'capacity': 1000,
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('machine_number', response.data)
        self.assertIn('installation_date', response.data)
        self.assertEqual(response.data['machine_number'], ['This field is required.'])
        self.assertEqual(response.data['installation_date'], ['This field is required.'])

    def test_add_elevator_missing_machine_number(self):
        url = reverse('maintenance_companies:add_elevator_to_building', 
                     kwargs={'company_uuid': self.company.id, 'building_uuid': self.building.id})

        data = {
            'user_name': 'LIFT3',
            'controller_type': 'Digital',
            'machine_type': 'gearless',
            'capacity': 1000,
            'manufacturer': 'Elevator Co.',
            'installation_date': '2025-01-01',
        }

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('machine_number', response.data)
        self.assertEqual(response.data['machine_number'], ['This field is required.'])

    def test_add_elevator_to_non_existing_building(self):
        non_existing_building_uuid = uuid4()
        url = reverse('maintenance_companies:add_elevator_to_building', 
                     kwargs={'company_uuid': self.company.id, 'building_uuid': non_existing_building_uuid})

        data = {
            'user_name': 'LIFT2',
            'controller_type': 'Analog',
            'machine_type': 'geared',
            'machine_number': 'LIFT002',
            'capacity': 1200,
            'manufacturer': 'Lift Inc.',
            'installation_date': '2025-01-01',
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_elevator_without_authentication(self):
        self.client.logout()
        url = reverse('maintenance_companies:add_elevator_to_building', 
                     kwargs={'company_uuid': self.company.id, 'building_uuid': self.building.id})

        data = {
            'user_name': 'LIFT1',
            'controller_type': 'Digital',
            'machine_type': 'gearless',
            'machine_number': 'LIFT001',
            'capacity': 1000,
            'manufacturer': 'Elevator Co.',
            'installation_date': '2025-01-01',
        }

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

