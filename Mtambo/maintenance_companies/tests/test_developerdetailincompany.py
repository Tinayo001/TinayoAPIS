from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from uuid import uuid4
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from developers.models import DeveloperProfile
from elevators.models import Elevator
from buildings.models import Building


class DeveloperDetailUnderCompanyViewTest(TestCase):

    def setUp(self):
        # Create a new User instance for each test to avoid unique constraint errors
        self.user = User.objects.create_user(
            email='testdeveloper@example.com',
            phone_number='1234567890',
            password='password123',
            first_name='John',
            last_name='Doe',
            account_type='developer'
        )

        # Create a new DeveloperProfile for this user
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name='Test Developer',
            address='123 Developer Ave',
            specialization='Elevators'
        )

        # Create MaintenanceCompanyProfile for the company
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Test Maintenance Co.',
            company_address='123 Test Street',
            registration_number='123ABC',
            specialization='Elevators'
        )

        # Create a Building instance with developer assigned
        self.building = Building.objects.create(
            name='Test Building',
            address='456 Building Lane',
            contact='123-456-7890',
            developer=self.developer  # Assign developer to the building
        )

        # Create Elevator instance related to the Building and Developer
        self.elevator = Elevator.objects.create(
            user_name='LIFT1',
            controller_type='Digital',
            machine_type='gearless',
            building=self.building,
            machine_number='LIFT123',
            capacity=1000,
            manufacturer='Test Manufacturer',
            installation_date='2022-01-01',
            maintenance_company=self.company,
            developer=self.developer
        ) 

        # URL to the view we are testing
        self.url = reverse('maintenance_companies:developer-detail-under-company', args=[self.company.id, self.developer.id])

    def test_get_developer_detail_success(self):
        """Test the successful retrieval of developer detail under a maintenance company"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('developer_name', response.data)
        self.assertEqual(response.data['developer_name'], 'Test Developer')
        self.assertEqual(response.data['specialization'], 'Elevators')

    def test_get_developer_detail_invalid_company(self):
        """Test if an invalid company ID returns 404 error"""
        invalid_company_id = uuid4()  # Random UUID not in the database
        url = reverse('maintenance_companies:developer-detail-under-company', args=[invalid_company_id, self.developer.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Maintenance company not found.')

    def test_get_developer_detail_invalid_developer(self):
        """Test if an invalid developer ID returns 404 error"""
        invalid_developer_id = uuid4()  # Random UUID not in the database
        url = reverse('maintenance_companies:developer-detail-under-company', args=[self.company.id, invalid_developer_id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Developer not found.')

    def test_get_developer_detail_developer_not_associated_with_building(self):
        """Test if a developer is not linked to any building under the specified company"""
        # Create a new developer for testing
        new_user = User.objects.create_user(
            email='newdeveloper@example.com',
            phone_number='0987654321',
            password='password123',
            first_name='Jane',
            last_name='Doe',
            account_type='developer'
        )
        
        # Create a new developer profile for this user
        new_developer = DeveloperProfile.objects.create(
            user=new_user,
            developer_name='New Developer',
            address='789 New Developer St.',
            specialization='Elevators'
        )
        
        # Do not associate this new developer with any building
        url = reverse('maintenance_companies:developer-detail-under-company', args=[self.company.id, new_developer.id])

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Developer not found or not linked to any buildings under the specified maintenance company.')

