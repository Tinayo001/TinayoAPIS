from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import Client

class SpecializationListViewTests(APITestCase):
    def setUp(self):
        """Set up test client and URLs"""
        self.client = Client()
        # Updated to use the correct URL name and namespace if needed
        self.specializations_url = reverse('specializations')  # If using namespace: reverse('api:specializations')
        self.expected_specializations = {
            "option1": "Elevators",
            "option2": "HVAC",
            "option3": "Power Backup Generators"
        }

    def test_get_specializations_success(self):
        """Test successful retrieval of specializations"""
        response = self.client.get(self.specializations_url)
        
        # Check status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response data structure
        self.assertIsInstance(response.data, dict)
        
        # Check if all expected specializations are present
        self.assertEqual(response.data, self.expected_specializations)
        
        # Check individual specializations
        self.assertEqual(response.data["option1"], "Elevators")
        self.assertEqual(response.data["option2"], "HVAC")
        self.assertEqual(response.data["option3"], "Power Backup Generators")

    def test_get_specializations_method_not_allowed(self):
        """Test that only GET method is allowed"""
        # Test POST request
        response = self.client.post(self.specializations_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test PUT request
        response = self.client.put(self.specializations_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Test DELETE request
        response = self.client.delete(self.specializations_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_response_structure(self):
        """Test the structure and content type of the response"""
        response = self.client.get(self.specializations_url)
        
        # Check content type
        self.assertTrue(
            response['Content-Type'].startswith('application/json')
        )
        
        # Verify all keys are present
        expected_keys = ["option1", "option2", "option3"]
        for key in expected_keys:
            self.assertIn(key, response.data)

