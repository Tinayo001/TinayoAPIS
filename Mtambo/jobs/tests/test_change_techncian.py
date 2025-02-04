from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from uuid import uuid4
from jobs.factories import UserFactory, MaintenanceCompanyProfileFactory, TechnicianProfileFactory, MaintenanceScheduleFactory

class ChangeTechnicianViewTest(APITestCase):

    def setUp(self):
        # Use factories to create test users and related objects
        self.user = UserFactory()
        self.maintenance_company = MaintenanceCompanyProfileFactory(user=self.user)
        self.technician = TechnicianProfileFactory(maintenance_company=self.maintenance_company)

        # Create a maintenance schedule object for testing
        self.maintenance_schedule = MaintenanceScheduleFactory(maintenance_company=self.maintenance_company)

        # Construct the URL for changing technician
        self.url = reverse('change-technician', kwargs={'schedule_type': 'regular', 'schedule_id': self.maintenance_schedule.id})

    def test_change_technician_success(self):
        # Create a new technician to reassign, ensuring the new technician is from the same maintenance company
        new_technician = TechnicianProfileFactory(maintenance_company=self.maintenance_company)

        # Data to send in the PUT request
        data = {
            "technician_id": str(new_technician.id)  # Make sure technician ID is a valid string UUID
        }

        response = self.client.put(self.url, data, format='json')

        # Debug the response for better insight
        print(response.data)  # You can use this to inspect the response data in the terminal

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Technician has been changed to", response.data["message"])

        # Check that the technician has been updated in the schedule
        self.maintenance_schedule.refresh_from_db()
        self.assertEqual(str(self.maintenance_schedule.technician.id), str(new_technician.id))
     
    def test_change_technician_invalid_schedule_type(self):
        # Test when an invalid schedule type is provided
        response = self.client.put(
            reverse('change-technician', kwargs={'schedule_type': 'invalid_type', 'schedule_id': self.maintenance_schedule.id}),
            {"technician_id": str(self.technician.id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid schedule type. Use 'regular', 'adhoc', or 'building'.")

    def test_change_technician_not_found(self):
        # Test when the maintenance schedule is not found
        non_existing_schedule_id = uuid4()
        response = self.client.put(
            reverse('change-technician', kwargs={'schedule_type': 'regular', 'schedule_id': non_existing_schedule_id}),
            {"technician_id": str(self.technician.id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], "Maintenance schedule not found.")

    def test_change_technician_invalid_technician_id(self):
        # Test with invalid technician_id format (not a valid UUID)
        response = self.client.put(
            self.url,
            {"technician_id": "invalid-technician-id"},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid Technician ID format. Must be a valid UUID.")

    def test_change_technician_technician_not_found(self):
        # Test when the technician doesn't exist
        non_existing_technician_id = uuid4()
        response = self.client.put(
            self.url,
            {"technician_id": str(non_existing_technician_id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["detail"], f"Technician with ID {non_existing_technician_id} does not exist.")

    def test_change_technician_technician_from_different_company(self):
        # Ensure the schedule is not completed so that the technician-company check is reached
        self.maintenance_schedule.status = 'scheduled'
        self.maintenance_schedule.save()

        # Test when technician is from a different company
        another_company = MaintenanceCompanyProfileFactory()
        another_technician = TechnicianProfileFactory(maintenance_company=another_company)

        response = self.client.put(
            self.url,
            {"technician_id": str(another_technician.id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "Technician is not linked to the same maintenance company as this maintenance schedule."
        )
    
    def test_change_technician_completed_schedule(self):
        # Test if technician change is disallowed on completed schedules
        self.maintenance_schedule.status = 'completed'
        self.maintenance_schedule.save()

        response = self.client.put(
            self.url,
            {"technician_id": str(self.technician.id)},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "You cannot reassign a completed schedule.")

