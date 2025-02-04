from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile


class MaintenanceCompanyBySpecializationViewTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Set up test data for maintenance companies."""
        # Create users and maintenance company profiles
        user1 = User.objects.create_user(
            email="elevator@example.com",
            phone_number="1234567890",
            password="password123",
            account_type="maintenance"
        )
        cls.company1 = MaintenanceCompanyProfile.objects.create(
            user=user1,
            company_name="Elevator Masters",
            company_address="123 Test Street",
            registration_number="REG123",
            specialization="Elevators"
        )

        user2 = User.objects.create_user(
            email="hvac@example.com",
            phone_number="0987654321",
            password="password123",
            account_type="maintenance"
        )
        cls.company2 = MaintenanceCompanyProfile.objects.create(
            user=user2,
            company_name="HVAC Experts",
            company_address="456 Example Avenue",
            registration_number="REG456",
            specialization="HVAC"
        )

        user3 = User.objects.create_user(
            email="generator@example.com",
            phone_number="1122334455",
            password="password123",
            account_type="maintenance"
        )
        cls.company3 = MaintenanceCompanyProfile.objects.create(
            user=user3,
            company_name="Generator Gurus",
            company_address="789 Main Road",
            registration_number="REG789",
            specialization="Generators"
        )

    def test_filter_by_specialization_valid(self):
        """Test filtering maintenance companies by a valid specialization."""
        url = reverse('maintenance_companies:specialization-list', kwargs={'specialization': 'Elevators'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "Elevator Masters")

    def test_filter_by_specialization_case_insensitive(self):
        """Test filtering by specialization with case insensitivity."""
        url = reverse('maintenance_companies:specialization-list', kwargs={'specialization': 'eLeVaToRs'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "Elevator Masters")

    def test_filter_by_specialization_invalid(self):
        """Test filtering with an invalid specialization input."""
        url = reverse('maintenance_companies:specialization-list', kwargs={'specialization': '123Invalid'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filter_by_specialization_no_results(self):
        """Test filtering with a valid specialization that yields no results."""
        url = reverse('maintenance_companies:specialization-list', kwargs={'specialization': 'Plumbing'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filter_by_specialization_empty(self):
        """Test filtering with an empty specialization parameter."""
        url = reverse('maintenance_companies:specialization-list-empty')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

