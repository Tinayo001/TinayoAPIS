from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from buildings.models import Building
from developers.models import DeveloperProfile
from uuid import uuid4
from account.models import User

class GetBuildingDetailsViewTestCase(APITestCase):

    def setUp(self):
        # Set up the necessary objects for the test
        # Create a user
        self.user = User.objects.create_user(
            email="developer@example.com", 
            phone_number="123456789", 
            password="password", 
            first_name="John", 
            last_name="Doe",
            account_type="developer"
        )

        # Create a developer profile associated with the user
        self.developer = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="123 Developer Street",
            specialization="Construction"
        )

        # Create a building associated with the developer
        self.building = Building.objects.create(
            name="Building 1", 
            address="Address 1", 
            contact="123", 
            developer=self.developer, 
            developer_name="Test Developer"
        )

        # URL for the building details view
        self.url = reverse('get_building_details', kwargs={'building_id': self.building.id})

    def test_get_building_details_success(self):
        """
        Test retrieving building details successfully.
        """
        response = self.client.get(self.url)
    
        # Ensure the response is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the building details returned match the created building
        self.assertEqual(response.data['id'], str(self.building.id))
        self.assertEqual(response.data['name'], self.building.name)
        self.assertEqual(response.data['address'], self.building.address)
        self.assertEqual(response.data['contact'], self.building.contact)
    
        # Modify the test to correctly access 'developer_name' inside the 'developer' dictionary
        self.assertEqual(response.data['developer']['developer_name'], self.building.developer_name)
    
    def test_get_building_details_not_found(self):
        """
        Test attempting to retrieve a building that doesn't exist (invalid UUID).
        """
        invalid_uuid = uuid4()  # Random UUID not in the database
        url = reverse('get_building_details', kwargs={'building_id': invalid_uuid})

        response = self.client.get(url)
        
        # Ensure the response is 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Building not found.")

    def test_get_building_details_invalid_uuid(self):
        """
        Test attempting to retrieve a building with an invalid UUID format.
        When using <uuid:building_id> in URLs, Django returns 404 for invalid UUIDs.
        """
        invalid_uuid = "invalid-uuid-format"
        url = f'/api/buildings/{invalid_uuid}/'
        response = self.client.get(url)
    
        # With <uuid:building_id> URL pattern, invalid UUIDs result in 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) 
     

