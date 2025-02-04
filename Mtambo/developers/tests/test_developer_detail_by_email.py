from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from account.models import User
from developers.models import DeveloperProfile
from rest_framework.exceptions import NotFound

class DeveloperDetailByEmailViewTestCase(APITestCase):
    """
    Test suite for the DeveloperDetailByEmailView to retrieve developer details by email.
    """
    
    def setUp(self):
        """
        Setup the test environment by creating users and their developer profiles.
        """
        # Create users with developer account_type
        self.user_1 = User.objects.create_user(
            email="developer1@example.com",
            phone_number="1234567890",
            password="password123",
            first_name="John",
            last_name="Doe",
            account_type="developer"
        )
        self.user_2 = User.objects.create_user(
            email="developer2@example.com",
            phone_number="9876543210",
            password="password123",
            first_name="Jane",
            last_name="Doe",
            account_type="developer"
        )

        # Create developer profiles for users
        self.developer_profile_1 = DeveloperProfile.objects.create(
            user=self.user_1,
            developer_name="John Developer",
            address="123 Main St",
            specialization="Web Development"
        )
        self.developer_profile_2 = DeveloperProfile.objects.create(
            user=self.user_2,
            developer_name="Jane Developer",
            address="456 Side St",
            specialization="Mobile Development"
        )

        # URL for the test
        self.url_1 = reverse('developer-detail-by-email', kwargs={'developer_email': self.user_1.email})
        self.url_2 = reverse('developer-detail-by-email', kwargs={'developer_email': self.user_2.email})
        self.invalid_email_url = reverse('developer-detail-by-email', kwargs={'developer_email': 'invalid@example.com'})

    def test_get_developer_by_email_valid(self):
        """
        Test retrieving a developer by a valid email.
        """
        response = self.client.get(self.url_1)
    
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user_1.id)  # Assuming user field returns the ID
        self.assertEqual(response.data['developer_name'], self.developer_profile_1.developer_name)
        self.assertEqual(response.data['address'], self.developer_profile_1.address)
        self.assertEqual(response.data['specialization'], self.developer_profile_1.specialization)
    
    def test_get_developer_by_email_invalid(self):
        """
        Test retrieving a developer by an email that does not exist.
        """
        response = self.client.get(self.invalid_email_url)
        
        # Expect a 404 Not Found error because the developer doesn't exist
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Developer with this email not found.")

    def test_get_developer_by_email_not_found(self):
        """
        Test retrieving a developer by a non-existing email.
        """
        non_existent_email_url = reverse('developer-detail-by-email', kwargs={'developer_email': 'nonexistent@example.com'})
        response = self.client.get(non_existent_email_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Developer with this email not found.")

    def test_get_developer_invalid_email_format(self):
        """
        Test retrieving a developer by an invalid email format.
        """
        invalid_email_format_url = reverse('developer-detail-by-email', kwargs={'developer_email': 'invalidemail'})
        response = self.client.get(invalid_email_format_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], "Developer with this email not found.")

