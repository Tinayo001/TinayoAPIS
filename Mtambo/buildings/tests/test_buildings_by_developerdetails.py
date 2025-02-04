from rest_framework import status
from django.urls import reverse
from rest_framework.test import APITestCase
from uuid import uuid4
from buildings.models import Building
from developers.models import DeveloperProfile
from account.models import User


class GetBuildingsByDeveloperViewTestCase(APITestCase):
    def setUp(self):
        """
        Set up test data for the developer and buildings.
        Creates a developer and exactly two buildings associated with the developer.
        """
        # Create a new developer user and profile
        self.developer_user = User.objects.create_user(
            email="developer@example.com", 
            phone_number="123456789", 
            password="password", 
            first_name="John", 
            last_name="Doe",
            account_type="developer"
        )

        self.developer = DeveloperProfile.objects.create(
            user=self.developer_user,
            developer_name="Test Developer",
            address="123 Developer Street",
            specialization="Construction"
        )

        # Clean up any pre-existing buildings in the test database
        Building.objects.all().delete()

        # Create exactly two buildings for the developer
        self.building1 = Building.objects.create(
            name="Building 1", 
            address="Address 1", 
            contact="123", 
            developer=self.developer, 
            developer_name="Test Developer"
        )
        self.building2 = Building.objects.create(
            name="Building 2", 
            address="Address 2", 
            contact="456", 
            developer=self.developer, 
            developer_name="Test Developer"
        )

        self.developer_id = self.developer.id  # Save developer id for reuse

    def test_get_buildings_by_developer_valid(self):
        """
        Test retrieving buildings for a valid developer.
        Ensures pagination works if applicable.
        """
        # Inspect the database before making the request
        print(f"DEBUG: Developer {self.developer_id} has buildings:")
        buildings = Building.objects.filter(developer=self.developer)
        for building in buildings:
            print(f"DEBUG: Building ID: {building.id}, Name: {building.name}")

        # Call the API endpoint to retrieve the developer's buildings
        url = reverse('get_buildings_by_developer', kwargs={'developer_id': self.developer_id}) + "?page=1&page_size=2"
        response = self.client.get(url)

        # Debugging response data to check what is returned
        print(f"DEBUG: Response data - {response.data}")

        # Assert that the response status is OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the pagination metadata is present
        self.assertIn('count', response.data)  # Total number of buildings
        self.assertIn('next', response.data)   # URL for next page (if any)
        self.assertIn('previous', response.data)  # URL for previous page (if any)

        # Assert the correct number of buildings are returned in the 'results' section (2 buildings per page)
        self.assertEqual(len(response.data['results']), 2)  # 2 buildings per page

        # Ensure the pagination is functioning correctly
        self.assertEqual(response.data['count'], 2)  # Total count of buildings (not more than 2)

    def test_get_buildings_by_developer_invalid_uuid(self):
        """
        Test when an invalid developer UUID is provided.
        This test ensures the reverse lookup works only with valid UUIDs.
        """
        invalid_uuid = "invalid-uuid-format"
        
        # Ensure the reverse lookup fails for invalid UUID format
        try:
            url = reverse('get_buildings_by_developer', kwargs={'developer_id': invalid_uuid})
        except Exception as e:
            url = None
        
        self.assertIsNone(url)
        # This ensures that an invalid UUID doesn't pass and doesn't trigger a reverse error

    def test_get_buildings_by_developer_not_found(self):
        """
        Test when no buildings exist for a developer.
        This test ensures that a 404 is returned when no buildings are found for the developer.
        """
        # Create a new user and developer profile
        new_user = User.objects.create_user(
            email="newdeveloper@example.com", 
            phone_number="987654321", 
            password="password", 
            first_name="Alice", 
            last_name="Smith",
            account_type="developer"
        )

        new_developer = DeveloperProfile.objects.create(
            user=new_user,
            developer_name="New Developer",
            address="456 Developer Street",
            specialization="Plumbing"
        )

        # URL for the new developer's buildings
        url = reverse('get_buildings_by_developer', kwargs={'developer_id': new_developer.id})

        response = self.client.get(url)

        # Ensure the response is 404 Not Found when no buildings are found for the developer
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "No buildings found for this developer.")

    def test_get_buildings_by_developer_pagination(self):
        """
        Test pagination of buildings (if pagination is implemented).
        """
        # Create a third building for the same developer
        Building.objects.create(
            name="Building 3", 
            address="Address 3", 
            contact="789", 
            developer=self.developer, 
            developer_name="Test Developer"
        )

        # URL for the buildings by developer endpoint with pagination parameters
        url = reverse('get_buildings_by_developer', kwargs={'developer_id': self.developer_id}) + "?page=1&page_size=2"

        response = self.client.get(url)

        # Debug the paginated response
        print(f"DEBUG: Paginated response data - {response.data}")

        # Ensure the response is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the response contains paginated results (2 buildings per page)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)

        # Ensure pagination metadata is present
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)

    def test_get_buildings_by_developer_invalid_developer(self):
        """
        Test when an invalid developer UUID is provided.
        """
        invalid_developer_id = uuid4()  # Using an invalid developer UUID

        url = reverse('get_buildings_by_developer', kwargs={'developer_id': invalid_developer_id})

        response = self.client.get(url)

        # Ensure the response is 404 Not Found when the developer is invalid
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], "Developer not found.")

