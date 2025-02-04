from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from account.models import User
from developers.models import DeveloperProfile
import uuid

class DeveloperDetailViewTestCase(APITestCase):
    def setUp(self):
        """
        Set up a user and developer profile for testing.
        """
        # Create a user (developer)
        self.user = User.objects.create_user(
            email="developer@example.com",
            phone_number="123456789",
            password="password",
            first_name="John",
            last_name="Doe",
            account_type="developer"
        )

        # Create a developer profile associated with the user
        self.developer_profile = DeveloperProfile.objects.create(
            user=self.user,
            developer_name="Test Developer",
            address="123 Developer Street",
            specialization="Construction"
        )

        # URL for retrieving a developer profile
        self.url = reverse('developer-detail', kwargs={'developer_id': self.developer_profile.id})

    def test_get_developer_valid(self):
        """
        Test retrieving a developer by a valid UUID.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Ensure the response contains the expected data
        self.assertEqual(response.data['id'], str(self.developer_profile.id))
        self.assertEqual(response.data['developer_name'], self.developer_profile.developer_name)
        self.assertEqual(response.data['address'], self.developer_profile.address)
        self.assertEqual(response.data['specialization'], self.developer_profile.specialization)

    def test_get_developer_invalid_uuid_format(self):
        """
        Test when an invalid UUID format is provided.
        Since we're using <uuid:developer_id> in the URL pattern,
        Django will return 404 for invalid UUID formats before reaching our view.
        """
        invalid_uuid = "invalid-uuid-format"
    
        # Manually construct the URL with the invalid UUID format
        url = f"/api/developers/{invalid_uuid}/"
        response = self.client.get(url)
    
        # When using <uuid:developer_id>, Django returns 404 for invalid UUID formats
        self.assertEqual(response.status_code, 404) 

    def test_get_developer_not_found(self):
        """
        Test when the developer does not exist (but UUID format is valid).
        """
        non_existent_uuid = uuid.uuid4()
        url = reverse('developer-detail', kwargs={'developer_id': non_existent_uuid})
        response = self.client.get(url)
    
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Developer not found", str(response.data)) 

