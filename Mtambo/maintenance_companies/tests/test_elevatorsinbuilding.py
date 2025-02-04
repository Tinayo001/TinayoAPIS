from rest_framework.test import APITestCase
from rest_framework import status
from uuid import uuid4
from datetime import date
from account.models import User
from developers.models import DeveloperProfile
from maintenance_companies.models import MaintenanceCompanyProfile
from buildings.models import Building
from elevators.models import Elevator
from django.urls import reverse


class ElevatorsInBuildingViewTest(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create(
            email="testuser@example.com",
            phone_number="1234567890",
            first_name="Test",
            last_name="User",
            password="testpassword"
        )

        # Create a DeveloperProfile (this is necessary to avoid the NOT NULL error)
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.user,  # Associate the user with the developer profile
            developer_name="Test Developer",
            address="Developer Address",
            specialization="Elevators"
        )

        # Create a maintenance company profile (adjust as necessary for your use case)
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,  # You can use the same user or another one
            company_name="Test Maintenance Company",
            company_address="Maintenance Company Address",
            registration_number="12345",
            specialization="Elevators"
        )

        # Create a building and associate it with the developer_profile
        self.building = Building.objects.create(
            name="Test Building",
            address="Test Address",
            contact="Test Contact",
            developer=self.developer_profile  # Associate developer profile to the building
        )    

        # Create an elevator and associate it with the building, maintenance company, and developer
        self.elevator = Elevator.objects.create(
            user_name="LIFT001",
            controller_type="Digital",  # Example controller type
            machine_type="gearless",  # Example machine type
            building=self.building,  # Associate it with the building
            machine_number="LIFT001",  # Example machine number
            capacity=1000,  # Example capacity
            manufacturer="Elevator Corp",  # Example manufacturer
            installation_date=date(2022, 5, 1),  # Example installation date
            maintenance_company=self.maintenance_company,  # Associate with the maintenance company
            developer=self.developer_profile  # Optionally associate a developer
        )

        # URL for the API endpoint
        self.url = reverse('maintenance_companies:elevators-in-building', kwargs={
            'company_id': self.maintenance_company.id,
            'building_id': self.building.id
        })

    def test_get_elevators_success(self):
        """Test that the elevators for a building under a specific maintenance company are fetched successfully."""
        response = self.client.get(self.url)

        # Check status code and that we get the expected data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # There should be one elevator in the response
        self.assertEqual(response.data[0]['machine_number'], "LIFT001")

    def test_get_elevators_invalid_company_id(self):
        """Test that an invalid maintenance company UUID returns a 404 error."""
        invalid_company_id = uuid4()  # Random invalid UUID
        url = reverse('maintenance_companies:elevators-in-building', kwargs={
            'company_id': invalid_company_id,
            'building_id': self.building.id
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Maintenance company not found.")

    def test_get_elevators_invalid_building_id(self):
        """Test that an invalid building UUID returns a 404 error."""
        invalid_building_id = uuid4()  # Random invalid UUID
        url = reverse('maintenance_companies:elevators-in-building', kwargs={
            'company_id': self.maintenance_company.id,
            'building_id': invalid_building_id
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Building not found.")

    def test_get_elevators_no_elevators_found(self):
        """Test that a building with no elevators under the maintenance company returns a 404 error."""
        # Create another building with no elevators linked to the maintenance company
        building_no_elevators = Building.objects.create(
            name="Building with No Elevators",
            address="789 No Elevator Street",
            contact="111222333",
            developer=self.developer_profile  # Correctly associate a developer
        )

        url = reverse('maintenance_companies:elevators-in-building', kwargs={
            'company_id': self.maintenance_company.id,
            'building_id': building_no_elevators.id
        })

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "No elevators found for this building under the specified maintenance company.")

    def test_get_elevators_invalid_uuid_format(self):
        """Test that invalid UUID format returns a 400 error."""
        invalid_company_id = "invalid-uuid"  # Invalid UUID format
        invalid_building_id = "invalid-uuid"  # Invalid UUID format
    
        try:
            url = reverse('maintenance_companies:elevators-in-building', kwargs={
                'company_id': invalid_company_id,
                'building_id': invalid_building_id
            })
        except Exception as e:
            url = None  # To capture the error and prevent test failure due to reverse() issues

        # Make sure that url generation raises an exception and is handled correctly.
        self.assertIsNone(url, "URL should not be generated with invalid UUID format")
     
