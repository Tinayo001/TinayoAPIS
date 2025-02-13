from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from uuid import uuid4
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from developers.models import DeveloperProfile
from elevators.models import Elevator
from buildings.models import Building


class BuildingsUnderDeveloperViewTest(TestCase):

    def setUp(self):
        # Create a user for testing
        self.user = User.objects.create_user(
            email='testuser@example.com',
            phone_number='1234567890',
            password='password123',
            first_name='John',
            last_name='Doe',
            account_type='developer'
        )

        # Create a maintenance company
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Maintenance Co.',
            company_address='123 Test Street',
            registration_number='123ABC',
            specialization='Elevators'
        )

        # Create a developer
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name='Test Developer',
            address='123 Developer Ave',
            specialization='Elevators'
        )

        # Create multiple buildings for testing
        self.buildings = []
        for i in range(3):
            building = Building.objects.create(
                name=f'Test Building {i}',
                address=f'456 Building Lane {i}',
                contact='123-456-7890',
                developer=self.developer
            )
            self.buildings.append(building)

            # Create elevator for each building
            Elevator.objects.create(
                user_name=f'LIFT{i}',
                controller_type='Digital',
                machine_type='gearless',
                building=building,
                machine_number=f'LIFT123_{i}',
                capacity=1000,
                manufacturer='Test Manufacturer',
                installation_date='2022-01-01',
                maintenance_company=self.company,
                developer=self.developer
            )

        # URL for the view we're testing
        self.url = reverse('maintenance_companies:buildings-under-developer', 
                          kwargs={
                              'company_id': str(self.company.id),
                              'developer_id': str(self.developer.id)
                          })

    def test_get_buildings_success(self):
        """Test successful retrieval of buildings under a developer and maintenance company"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Should return all 3 buildings
        
        # Verify building data
        for building_data in response.data:
            self.assertIn('name', building_data)
            self.assertIn('address', building_data)
            self.assertIn('contact', building_data)

    def test_get_buildings_invalid_company_id(self):
        """Test response with invalid company ID"""
        invalid_company_id = uuid4()
        url = reverse('maintenance_companies:buildings-under-developer',
                     kwargs={
                         'company_id': str(invalid_company_id),
                         'developer_id': str(self.developer.id)
                     })

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Maintenance company not found.')

    def test_get_buildings_invalid_developer_id(self):
        """Test response with invalid developer ID"""
        invalid_developer_id = uuid4()
        url = reverse('maintenance_companies:buildings-under-developer',
                     kwargs={
                         'company_id': str(self.company.id),
                         'developer_id': str(invalid_developer_id)
                     })

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Developer not found.')

    def test_get_buildings_no_buildings_found(self):
        """Test response when no buildings are found"""
        # Create new developer with no buildings
        new_user = User.objects.create_user(
            email='newdev@example.com',
            phone_number='9876543210',
            password='password123',
            first_name='Jane',
            last_name='Doe',
            account_type='developer'
        )
        
        new_developer = DeveloperProfile.objects.create(
            user=new_user,
            developer_name='New Developer',
            address='789 New Ave',
            specialization='Elevators'
        )

        url = reverse('maintenance_companies:buildings-under-developer',
                     kwargs={
                         'company_id': str(self.company.id),
                         'developer_id': str(new_developer.id)
                     })

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 'No buildings found for this developer and maintenance company.')         
