import uuid
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from maintenance_companies.models import MaintenanceCompanyProfile
from elevators.models import Elevator
from buildings.models import Building
from developers.models import DeveloperProfile
from technicians.models import TechnicianProfile

# Define the User model
User = get_user_model()

class ElevatorsUnderCompanyViewTestCase(APITestCase):

    def setUp(self):
        """
        This method is called before every test to set up any state that is shared across tests.
        """
        # Create a user (this could be a Maintenance user)
        self.user = User.objects.create_user(
            email="maintenance@example.com",
            phone_number="1234567890",
            password="password",
            first_name="John",
            last_name="Doe",
            account_type="maintenance"
        )
        
        # Create a Developer profile (needed for the Building model)
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="123 Developer Street",
            specialization="Elevators"
        )
        
        # Create a MaintenanceCompanyProfile for this user
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name="Test Maintenance Company",
            company_address="123 Test Street",
            registration_number="REG12345",
            specialization="Elevators"
        )
        
        # Create a building instance with the developer
        self.building = Building.objects.create(
            name="Test Building",
            address="456 Test Ave",
            contact="9876543210",
            developer=self.developer,
            developer_name="Test Developer"
        )

        # Create some elevators for the maintenance company and associated with the building
        self.elevator_1 = Elevator.objects.create(
            user_name="Lift 1",
            controller_type="Digital",
            machine_type="gearless",
            building=self.building,
            machine_number="LIFT001",
            capacity=1000,
            manufacturer="Test Manufacturer",
            installation_date="2023-01-01",
            maintenance_company=self.company,
        )

        self.elevator_2 = Elevator.objects.create(
            user_name="Lift 2",
            controller_type="Analog",
            machine_type="geared",
            building=self.building,
            machine_number="LIFT002",
            capacity=1500,
            manufacturer="Test Manufacturer",
            installation_date="2023-02-01",
            maintenance_company=self.company,
        )

        # Initialize the APIClient for making requests
        self.client = APIClient()

    def test_get_elevators_under_company(self):
        """
        Test retrieving the list of elevators for a specific maintenance company.
        """
        url = f"/api/maintenance-companies/elevators/{self.company.id}/"
        
        # Make a GET request to the API
        response = self.client.get(url)
        
        # Check that the response status code is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the correct elevators are returned
        data = response.json()
        self.assertEqual(len(data), 2)  # We created 2 elevators
        
        # Check if the elevator data contains the correct information
        elevator_1_data = data[0]
        self.assertEqual(elevator_1_data['machine_number'], "LIFT001")
        self.assertEqual(elevator_1_data['user_name'], "Lift 1")
        self.assertEqual(elevator_1_data['controller_type'], "Digital")
        
        elevator_2_data = data[1]
        self.assertEqual(elevator_2_data['machine_number'], "LIFT002")
        self.assertEqual(elevator_2_data['user_name'], "Lift 2")
        self.assertEqual(elevator_2_data['controller_type'], "Analog")

    def test_get_no_elevators_for_company(self):
        """
        Test that the API returns a 404 response when no elevators are found for a company.
        """
        # Create a new unique user for this test
        new_user = User.objects.create_user(
            email="new_maintenance@example.com",
            phone_number="0987654321",
            password="password",
            first_name="Jane",
            last_name="Smith",
            account_type="maintenance"
        )
    
        # Create a new MaintenanceCompanyProfile for this new user
        new_company = MaintenanceCompanyProfile.objects.create(
            user=new_user,
            company_name="New Maintenance Company",
            company_address="789 New Street",
            registration_number="REG67890",
            specialization="Elevators"
        )
    
        url = f"/api/maintenance-companies/elevators/{new_company.id}/"
    
        # Make a GET request to the API
        response = self.client.get(url)
    
        # Check that the response status code is 404 NOT FOUND
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
        # Check the response message (based on how your API returns the response)
        data = response.json()
        self.assertIn('message', data)  # Look for 'message' or the appropriate field
        self.assertEqual(data['message'], "No elevators found for this building under the specified maintenance company.")
     
    
    def test_get_invalid_company_id(self):
        """
        Test that the API returns a 404 response for an invalid company UUID.
        """
        # Use an invalid UUID
        invalid_uuid = uuid.uuid4()

        url = f"/api/maintenance-companies/elevators/{invalid_uuid}/"
    
        # Make a GET request to the API
        response = self.client.get(url)
    
        # Check that the response status code is 404 NOT FOUND
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
        # Check the response message (it will now be 'No MaintenanceCompanyProfile matches the given query.')
        data = response.json()
        self.assertIn('detail', data)  # DRF typically uses 'detail' for error messages
        self.assertEqual(data['detail'], "No MaintenanceCompanyProfile matches the given query.")
    
