from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from buildings.models import Building
from developers.models import DeveloperProfile

class ListBuildingsViewTestCase(APITestCase):

    def setUp(self):
        # Clear any existing data
        Building.objects.all().delete()

        # Create 2 buildings for testing
        developer = DeveloperProfile.objects.create(developer_name="Test Developer")
        Building.objects.create(name="Building 1", address="Address 1", contact="123", developer=developer)
        Building.objects.create(name="Building 2", address="Address 2", contact="456", developer=developer)

        # URL for the list buildings view
        self.url = reverse('list_buildings')

    def test_list_buildings_success(self):
        """
        Test retrieving the list of buildings
        """
        response = self.client.get(self.url)

        # Check the number of buildings returned
        self.assertEqual(len(response.data['results']), 2)

    def test_list_buildings_no_data(self):
        """
        Test retrieving buildings when none exist
        """
        # Delete the created buildings
        Building.objects.all().delete()

        response = self.client.get(self.url)

        # Check if 'results' is an empty list
        self.assertEqual(response.data['results'], [])

    def test_list_buildings_invalid_endpoint(self):
        """
        Test hitting an invalid endpoint for the buildings list
        """
        # Directly use a URL that doesn't exist (simulating an invalid endpoint)
        invalid_url = '/api/invalid-endpoint/'
        response = self.client.get(invalid_url)

        # Ensure we get a 404 response
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

