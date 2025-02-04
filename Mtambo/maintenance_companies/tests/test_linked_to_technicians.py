from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from uuid import uuid4
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from elevators.models import Elevator
from account.models import User
from buildings.models import Building
from developers.models import DeveloperProfile

class ElevatorsUnderTechnicianViewTest(APITestCase):
    @staticmethod
    def get_unique_phone_number():
        """Helper function to generate unique phone numbers"""
        import random
        return f"12345678{random.randint(1000, 9999)}"

    def setUp(self):
        """
        Setup initial data for tests, including DeveloperProfile.
        """
        # Create a user for maintenance company
        self.maintenance_user = User.objects.create_user(
            email="maintenance_user@example.com",
            phone_number=self.get_unique_phone_number(),
            password="password123",
            first_name="Maintenance",
            last_name="User",
            account_type="maintenance"
        )

        # Create a user for technician
        self.technician_user = User.objects.create_user(
            email="technician_user@example.com",
            phone_number=self.get_unique_phone_number(),
            password="password123",
            first_name="Technician",
            last_name="User",
            account_type="technician"
        )

        # Create a user for developer
        self.developer_user = User.objects.create_user(
            email="developer_user@example.com",
            phone_number=self.get_unique_phone_number(),
            password="password123",
            first_name="Developer",
            last_name="User",
            account_type="developer"
        )

        # Create Developer Profile
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.developer_user,
            developer_name="Tech Developers",
            address="789 Developer Rd",
            specialization="Elevators"
        )

        # Create a maintenance company profile
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.maintenance_user,
            company_name="Tech Elevators",
            company_address="123 Tech Lane",
            registration_number="T12345",
            specialization="Elevators"
        )

        # Create technician profile and link to the company
        self.technician = TechnicianProfile.objects.create(
            user=self.technician_user,
            specialization="Elevator Technician",
            maintenance_company=self.company
        )

        # Create a building instance linked to DeveloperProfile
        self.building = Building.objects.create(
            name="Tech Tower",
            address="456 Tech Blvd",
            contact="Tech Contact",
            developer=self.developer_profile,
            developer_name="Tech Developer"
        )

        # Create elevator assigned to the technician and company
        self.elevator = Elevator.objects.create(
            user_name="LIFT1",
            controller_type="Digital",
            machine_type="gearless",
            building=self.building,
            machine_number="LIFT1234",
            capacity=1000,
            manufacturer="TechLift",
            installation_date="2022-01-01",
            maintenance_company=self.company,
            technician=self.technician
        )

        # Create URL for the API endpoint
        self.url = reverse('maintenance_companies:elevators-under-technician', 
                         kwargs={'company_id': self.company.id, 
                                'technician_id': self.technician.id})

    def test_get_elevators_under_technician_success(self):
        """
        Test that we can retrieve elevators assigned to a technician
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Only one elevator assigned
        self.assertEqual(response.data[0]['machine_number'], self.elevator.machine_number)

    def test_get_elevators_under_technician_no_elevators(self):
        """
        Test that we return an appropriate message when there are no elevators assigned
        to the technician for the specified maintenance company.
        """
        # Create another technician without elevators assigned
        new_technician_user = User.objects.create_user(
            email="new_technician@example.com",
            phone_number=self.get_unique_phone_number(),
            password="password123",
            first_name="New",
            last_name="Technician",
            account_type="technician"
        )
        new_technician = TechnicianProfile.objects.create(
            user=new_technician_user,
            specialization="Elevator Technician",
            maintenance_company=self.company
        )

        url = reverse('maintenance_companies:elevators-under-technician', 
                     kwargs={'company_id': self.company.id, 
                            'technician_id': new_technician.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 
                        "No elevators found under this technician for the specified maintenance company.")

    def test_get_elevators_technician_not_found(self):
        """
        Test that we return an error when technician is not found
        """
        invalid_technician_id = uuid4()  # Generate a random UUID not in database
        url = reverse('maintenance_companies:elevators-under-technician', 
                     kwargs={'company_id': self.company.id, 
                            'technician_id': invalid_technician_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Technician not found.")

    def test_get_elevators_company_not_found(self):
        """
        Test that we return an error when the maintenance company is not found
        """
        invalid_company_id = uuid4()  # Generate a random UUID not in database
        url = reverse('maintenance_companies:elevators-under-technician', 
                     kwargs={'company_id': invalid_company_id, 
                            'technician_id': self.technician.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Maintenance company not found.")

    def test_get_elevators_internal_server_error(self):
        """
        Test that we return an error message when an internal server error occurs.
        This simulates an unexpected exception in the view.
        """
        # Simulate an internal error by mocking a failure in the code
        with self.assertRaises(Exception):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_get_elevators_no_technician_assigned(self):
        """
        Test case for when the elevator is not assigned to the technician
        but is linked to another technician.
        """
        # Create a new technician user
        new_technician_user = User.objects.create_user(
            email="another_technician@example.com",
            phone_number=self.get_unique_phone_number(),
            password="password123",
            first_name="Another",
            last_name="Technician",
            account_type="technician"
        )
        new_technician = TechnicianProfile.objects.create(
            user=new_technician_user,
            specialization="Elevator Technician",
            maintenance_company=self.company
        )

        # Reassign the elevator to the new technician
        self.elevator.technician = new_technician
        self.elevator.save()

        # Now fetch the elevators assigned to the old technician
        url = reverse('maintenance_companies:elevators-under-technician', 
                     kwargs={'company_id': self.company.id, 
                            'technician_id': self.technician.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], 
                        "No elevators found under this technician for the specified maintenance company.")
        
    def test_get_technician_without_maintenance_company(self):
        """
        Test case for a technician not linked to any maintenance company
        """
        # Create new user for technician without company
        technician_user_without_company = User.objects.create_user(
            email="technician_no_company@example.com",
            phone_number=self.get_unique_phone_number(),
            password="password123",
            first_name="No Company",
            last_name="Technician",
            account_type="technician"
        )
    
        technician_without_company = TechnicianProfile.objects.create(
            user=technician_user_without_company,
            specialization="Elevator Technician"
        )

        url = reverse('maintenance_companies:elevators-under-technician', 
                    kwargs={'company_id': self.company.id, 
                            'technician_id': technician_without_company.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "No elevators found under this technician for the specified maintenance company.") 
