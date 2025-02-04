from unittest.mock import patch
from django.db import DatabaseError
from django.test import TestCase
from rest_framework import status
from django.urls import reverse
from uuid import uuid4
from maintenance_companies.models import MaintenanceCompanyProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule
from django.contrib.auth import get_user_model
from developers.models import DeveloperProfile
from technicians.models import TechnicianProfile

# Setup the test data
class RemoveMaintenanceFromBuildingElevatorsViewTestCase(TestCase):
    def setUp(self):
        """
        Set up the initial data required for the tests.
        """
        # Create a user (developer and maintenance company user)
        self.user = get_user_model().objects.create_user(
            email="testuser@example.com", phone_number="123456789", password="testpassword"
        )
        
        # Create DeveloperProfile linked to the user
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="123 Developer St.",
            specialization="Elevators"
        )
        
        # Create a MaintenanceCompanyProfile for the user
        self.maintenance_company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name="Test Maintenance Co.",
            company_address="123 Test St.",
            registration_number="TEST1234",
            specialization="Elevators"
        )
        
        # Create a TechnicianProfile linked to the Maintenance Company
        self.technician = TechnicianProfile.objects.create(
            user=self.user,
            specialization="Elevator Technician",
            maintenance_company=self.maintenance_company,
            is_approved=True
        )

        # Create a building and associate it with the developer
        self.building = Building.objects.create(
            name="Test Building",
            address="456 Test Ave",
            contact="John Doe",
            developer=self.developer,  # Fix: Associate the developer here
            developer_name="Test Developer"
        )
        
        # Create elevators linked to the building and maintenance company
        self.elevator1 = Elevator.objects.create(
            user_name="Elevator 1",
            machine_type="gearless",
            building=self.building,
            machine_number="E123",
            capacity=1000,
            manufacturer="Test Manufacturer",
            installation_date="2020-01-01",
            maintenance_company=self.maintenance_company
        )
        
        self.elevator2 = Elevator.objects.create(
            user_name="Elevator 2",
            machine_type="geared",
            building=self.building,
            machine_number="E124",
            capacity=1500,
            manufacturer="Test Manufacturer",
            installation_date="2021-01-01",
            maintenance_company=self.maintenance_company
        )

        # Create a maintenance schedule linked to the elevators
        self.schedule1 = MaintenanceSchedule.objects.create(
            elevator=self.elevator1,
            scheduled_date="2025-01-01 10:00:00",
            next_schedule="1_month",
            description="Scheduled maintenance",
            status="scheduled",
            maintenance_company=self.maintenance_company
        )

        self.schedule2 = MaintenanceSchedule.objects.create(
            elevator=self.elevator2,
            scheduled_date="2025-02-01 10:00:00",
            next_schedule="3_months",
            description="Scheduled maintenance",
            status="scheduled",
            maintenance_company=self.maintenance_company
        )

        # URL for the delete operation
        self.url = reverse('maintenance_companies:remove-maintenance-from-elevators', args=[self.maintenance_company.id, self.building.id])

    def test_remove_maintenance_from_building_elevators(self):
        """
        Test successful removal of the maintenance company and technician from elevators.
        """
        # Check the initial count of affected elevators and schedules
        initial_elevator_count = Elevator.objects.filter(maintenance_company=self.maintenance_company).count()
        initial_schedule_count = MaintenanceSchedule.objects.filter(maintenance_company=self.maintenance_company).count()
        
        # Send DELETE request
        response = self.client.delete(self.url)
        
        # Assert successful response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Successfully removed the maintenance company", response.data["message"])
        
        # Assert the maintenance company is removed from elevators
        self.assertEqual(Elevator.objects.filter(maintenance_company=self.maintenance_company).count(), initial_elevator_count - 2)
        
        # Assert the maintenance company is removed from schedules
        self.assertEqual(MaintenanceSchedule.objects.filter(maintenance_company=self.maintenance_company).count(), initial_schedule_count - 2)

    def test_maintenance_company_not_found(self):
        """
        Test the case where the maintenance company does not exist.
        """
        non_existent_company_id = uuid4()  # Generate a random UUID
        url = reverse('maintenance_companies:remove-maintenance-from-elevators', args=[non_existent_company_id, self.building.id])
        
        # Send DELETE request
        response = self.client.delete(url)
        
        # Assert 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Maintenance company not found.")

    def test_building_not_found(self):
        """
        Test the case where the building does not exist.
        """
        non_existent_building_id = uuid4()  # Generate a random UUID
        url = reverse('maintenance_companies:remove-maintenance-from-elevators', args=[self.maintenance_company.id, non_existent_building_id])
        
        # Send DELETE request
        response = self.client.delete(url)
        
        # Assert 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Building not found.")

    def test_no_elevators_linked_to_company(self):
        """
        Test the case where no elevators are linked to the maintenance company in the specified building.
        """
        # Create a building without elevators linked to the maintenance company
        other_building = Building.objects.create(
            name="Other Building",
            address="789 Other Ave",
            contact="Jane Doe",
            developer=self.developer,  # Make sure to associate the developer
            developer_name="Other Developer"
        )
        
        # Send DELETE request for the new building
        url = reverse('maintenance_companies:remove-maintenance-from-elevators', args=[self.maintenance_company.id, other_building.id])
        response = self.client.delete(url)
        
        # Assert 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No elevators linked to the provided maintenance company in this building.")

    def test_exception_handling(self):
        """
        Test the case where an unexpected exception occurs (e.g., database error).
        """
        # Simulate a DatabaseError by mocking the get_object method
        with patch('maintenance_companies.views.RemoveMaintenanceFromBuildingElevatorsView.get_object', side_effect=DatabaseError("Database error")):
            # Send DELETE request that will trigger the simulated error
            response = self.client.delete(self.url)

        # Assert that the response status is 500 Internal Server Error
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("Database error", response.data["error"]) 

