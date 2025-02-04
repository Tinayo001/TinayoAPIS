from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch

User = get_user_model()

class LoginViewTests(APITestCase):
    def setUp(self):
        # Create a test user with email and phone number
        self.user = User.objects.create_user(
            email='testuser@example.com',
            phone_number='1234567890',
            password='testpass123'
        )
        
        # URL for login endpoint
        self.login_url = reverse('login')
        
        # Valid credentials
        self.valid_email_payload = {
            'email_or_phone': 'testuser@example.com',
            'password': 'testpass123'
        }
        
        self.valid_phone_payload = {
            'email_or_phone': '1234567890',
            'password': 'testpass123'
        }
        
        self.invalid_credentials_payload = {
            'email_or_phone': 'testuser@example.com',
            'password': 'wrongpass'
        }

    def test_login_with_valid_email(self):
        """Test login with valid email credentials"""
        response = self.client.post(self.login_url, self.valid_email_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
    def test_login_with_valid_phone(self):
        """Test login with valid phone credentials"""
        # First ensure your authentication backend is properly configured
        response = self.client.post(self.login_url, self.valid_phone_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(
            self.login_url, 
            self.invalid_credentials_payload, 
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], 'Invalid credentials')

    def test_login_with_missing_fields(self):
        """Test login with missing required fields"""
        # Test with missing password
        response = self.client.post(
            self.login_url,
            {'email_or_phone': 'testuser@example.com'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        # Test with missing email_or_phone
        response = self.client.post(
            self.login_url,
            {'password': 'testpass123'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email_or_phone', response.data)

    def test_login_with_empty_fields(self):
        """Test login with empty fields"""
        response = self.client.post(
            self.login_url,
            {
                'email_or_phone': '',
                'password': ''
            },
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('account.views.authenticate')  # Assuming authenticate is imported in views.py
    def test_authentication_system_error(self, mock_authenticate):
        """Test system error during authentication"""
        mock_authenticate.return_value = None
    
        payload = {
            'email_or_phone': 'test@example.com',
            'password': 'testpass123'
        }
    
        response = self.client.post(
            self.login_url,
            payload,
            format='json'
        )
           
        mock_authenticate.assert_called_once()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['error'], 'Invalid credentials')
