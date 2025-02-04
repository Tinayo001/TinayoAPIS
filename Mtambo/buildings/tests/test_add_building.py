from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from uuid import uuid4
from account.models import User
from developers.models import DeveloperProfile
from buildings.models import Building

class AddBuildingViewTestCase(APITestCase):
    """Test suite for the AddBuildingView"""

    def setUp(self):
        """Setup initial test data"""

        # Create a developer user
        self.user = User.objects.create(
            first_name='John', 
            last_name='Doe', 
            email='john.doe@example.com', 
            phone_number='1234567890', 
            account_type='developer', 
            password='testpassword123'
        )

        # Create DeveloperProfile for the user
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.user,
            developer_name='Doe Developers',
            address='123 Developer Lane',
            specialization='Residential'
        )

        # The URL for the AddBuildingView API endpoint
        self.url = reverse('add-building')

    def test_create_building_success(self):
        """Test that a building is successfully created"""

        data = {
            "developer_id": str(self.developer_profile.id),
            "name": "Trump Towers",  # Changed from building_name to name
            "address": "Chicago Westside",
            "contact": "contact@trumptowers.com"
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        building = Building.objects.get(id=response.data['id'])
        self.assertEqual(building.name, "Trump Towers")
        self.assertEqual(building.address, "Chicago Westside")
        self.assertEqual(building.developer_name, "Doe Developers")

    def test_create_building_invalid_developer_id(self):
        """Test creating a building with an invalid developer ID"""

        invalid_developer_id = str(uuid4())

        data = {
            "developer_id": invalid_developer_id,
            "name": "Trump Towers",  # Changed from building_name to name
            "address": "Chicago Westside",
            "contact": "contact@trumptowers.com"
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Developer with ID', response.data['error'])

    def test_create_building_without_developer_name(self):
        """Test creating a building without providing a developer name"""

        data = {
            "developer_id": str(self.developer_profile.id),
            "name": "Sunset Apartments",  # Changed from building_name to name
            "address": "Los Angeles",
            "contact": "contact@sunsetapartments.com"
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        building = Building.objects.get(id=response.data['id'])
        self.assertEqual(building.developer_name, self.developer_profile.developer_name)

    def test_create_building_missing_fields(self):
        """Test creating a building with missing required fields"""

        data = {
            "developer_id": str(self.developer_profile.id),
            "name": "Trump Towers",  # Changed from building_name to name
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('address', response.data)

    def test_create_building_invalid_uuid_format(self):
        """Test creating a building with an invalid UUID format for developer_id"""

        data = {
            "developer_id": "invalid-uuid",
            "name": "Trump Towers",  # Changed from building_name to name
            "address": "Chicago Westside",
            "contact": "contact@trumptowers.com"
        }

        response = self.client.post(self.url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('developer_id', response.data)
