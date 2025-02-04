import uuid
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile

class TechnicianDetailForCompanyViewTest(APITestCase):

    def setUp(self):
        # Create a user for the maintenance company (this user should be the company owner)
        self.user = User.objects.create_user(
            email='maintenance@example.com',
            phone_number='1234567890',
            password='password123',
            first_name='John',
            last_name='Doe',
            account_type='maintenance'
        )
        
        # Create a Maintenance Company linked to the above user (ensure the user is the company owner)
        self.company = MaintenanceCompanyProfile.objects.create(
            user=self.user,
            company_name='Elevator Maintenance Ltd',
            company_address='123 Elevator St',
            registration_number='ELEV12345',
            specialization='Elevators'
        )
        
        # Create a technician linked to the above company
        self.technician_user = User.objects.create_user(
            email='technician@example.com',
            phone_number='9876543210',
            password='password456',
            first_name='Jane',
            last_name='Smith',
            account_type='technician'
        )
        
        self.technician = TechnicianProfile.objects.create(
            user=self.technician_user,
            specialization='Elevator Technician',
            maintenance_company=self.company,
            is_approved=True
        )

        # Log in the user (company owner) to access the technician details
        self.client.login(email=self.user.email, password='password123')

        # URL for the view - ensure the UUIDs are used properly
        self.url = reverse('maintenance_companies:technician-detail-for-company', 
                           kwargs={'company_uuid': self.company.id, 'technician_uuid': self.technician.id})

    def test_get_technician_details_valid(self):
        # Make a GET request to the view with valid data
        response = self.client.get(self.url)

        # Assert that the response is OK (200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Print the response data for debugging purposes
        print(response.data)

        # Assert that the returned data contains the correct technician details
        self.assertEqual(response.data['id'], str(self.technician.id))
        self.assertEqual(response.data['technician_name'], f"{self.technician_user.first_name} {self.technician_user.last_name}")
        self.assertEqual(response.data['specialization'], self.technician.specialization)
        self.assertEqual(response.data['maintenance_company_name'], self.company.company_name)
        self.assertEqual(response.data['email'], self.technician_user.email)
        self.assertEqual(response.data['phone_number'], self.technician_user.phone_number)

    def test_get_technician_details_invalid_company(self):
        # Use a non-existing company UUID
        invalid_company_uuid = uuid.uuid4()
        url = reverse('maintenance_companies:technician-detail-for-company', 
                      kwargs={'company_uuid': invalid_company_uuid, 'technician_uuid': self.technician.id})

        # Make a GET request to the view with an invalid company UUID
        response = self.client.get(url)

        # Assert that the response status code is 404 (Not Found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_technician_details_invalid_technician(self):
        # Use a non-existing technician UUID
        invalid_technician_uuid = uuid.uuid4()
        url = reverse('maintenance_companies:technician-detail-for-company', 
                      kwargs={'company_uuid': self.company.id, 'technician_uuid': invalid_technician_uuid})

        # Make a GET request to the view with an invalid technician UUID
        response = self.client.get(url)

        # Assert that the response status code is 404 (Not Found)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_technician_details_unauthorized(self):
        # Log out the current user to simulate an unauthorized request
        self.client.logout()
    
        # Print to ensure logout is effective
        print("Logged out:", self.client.session)

        # Make a GET request to the view without authentication
        response = self.client.get(self.url)

        # Assert that the response status code is 401 (Unauthorized)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
     

    def test_get_technician_details_forbidden(self):
        # Create another technician and assign to a different company
        another_user = User.objects.create_user(
            email='another_technician@example.com',
            phone_number='1112223333',
            password='password789',
            first_name='Tom',
            last_name='Jones',
            account_type='technician'
        )
        another_company = MaintenanceCompanyProfile.objects.create(
            user=another_user,
            company_name='Other Maintenance Ltd',
            company_address='456 Other St',
            registration_number='OTHER12345',
            specialization='Elevators'
        )
        another_technician = TechnicianProfile.objects.create(
            user=another_user,
            specialization='Elevator Technician',
            maintenance_company=another_company,
            is_approved=True
        )

        # Log in the original user (company owner) who should not have access to the other company's technician
        self.client.login(email=self.user.email, password='password123')

        # URL for accessing the technician of the other company
        forbidden_url = reverse('maintenance_companies:technician-detail-for-company', 
                                kwargs={'company_uuid': another_company.id, 'technician_uuid': another_technician.id})

        # Try to access the technician of another company
        response = self.client.get(forbidden_url)

        # Assert that the response status code is 403 (Forbidden)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

