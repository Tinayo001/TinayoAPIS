from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from uuid import uuid4
from django.utils import timezone

from jobs.models import (
    BuildingLevelAdhocSchedule,
    AdHocMaintenanceSchedule,
    AdHocElevatorConditionReport,
    AdHocMaintenanceLog
)
from jobs.factories import (
    BuildingFactory,
    ElevatorFactory,
    TechnicianProfileFactory,
    MaintenanceCompanyProfileFactory,
    BuildingLevelAdhocScheduleFactory
)

class CompleteBuildingScheduleViewTests(APITestCase):
    def setUp(self):
        # Create base objects
        self.maintenance_company = MaintenanceCompanyProfileFactory()
        self.technician = TechnicianProfileFactory(
            maintenance_company=self.maintenance_company
        )
        self.building = BuildingFactory()
        
        # Create multiple elevators for the building
        self.elevators = [
            ElevatorFactory(
                building=self.building,
                maintenance_company=self.maintenance_company,
                technician=self.technician
            ) for _ in range(3)
        ]
        
        # Create building schedule
        self.building_schedule = BuildingLevelAdhocScheduleFactory(
            building=self.building,
            technician=self.technician,
            maintenance_company=self.maintenance_company,
            status='scheduled'
        )
        
        # Updated URL path construction
        self.url = f'/api/jobs/buildings/{self.building_schedule.id}/complete-schedule/'

        # Create valid test data
        self.valid_elevator_data = {
            "components_checked": "Doors, Motor, Safety Brakes",
            "condition": "Good working condition",
            "summary_title": "Regular maintenance",
            "description": "Completed all checks",
            "overseen_by": "John Supervisor"
        }

    def _create_elevator_payload(self, elevator_id, include_all_fields=True):
        """Helper method to create payload for a single elevator"""
        if include_all_fields:
            return {
                "elevator_id": str(elevator_id),
                "condition_report": {
                    "components_checked": self.valid_elevator_data["components_checked"],
                    "condition": self.valid_elevator_data["condition"]
                },
                "maintenance_log": {
                    "summary_title": self.valid_elevator_data["summary_title"],
                    "description": self.valid_elevator_data["description"],
                    "overseen_by": self.valid_elevator_data["overseen_by"]
                }
            }
        return {"elevator_id": str(elevator_id)}

    def test_successful_completion(self):
        """Test successful completion of building schedule with valid data"""
        data = {
            "elevators": [
                self._create_elevator_payload(elevator.id)
                for elevator in self.elevators
            ]
        }

        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.building_schedule.refresh_from_db()
        self.assertEqual(self.building_schedule.status, 'completed')
        
        # Verify creation of related objects
        for elevator in self.elevators:
            # Check AdHocMaintenanceSchedule was created
            adhoc_schedule = AdHocMaintenanceSchedule.objects.get(
                elevator=elevator,
                status='completed'
            )
            
            # Check condition report was created with correct values
            condition_report = AdHocElevatorConditionReport.objects.get(
                ad_hoc_schedule=adhoc_schedule
            )
            self.assertEqual(condition_report.components_checked, self.valid_elevator_data["components_checked"])
            self.assertEqual(condition_report.condition, self.valid_elevator_data["condition"])
            
            # Check maintenance log was created with correct values
            maintenance_log = AdHocMaintenanceLog.objects.get(
                ad_hoc_schedule=adhoc_schedule
            )
            self.assertEqual(maintenance_log.summary_title, self.valid_elevator_data["summary_title"])
            self.assertEqual(maintenance_log.description, self.valid_elevator_data["description"])
            self.assertEqual(maintenance_log.overseen_by, self.valid_elevator_data["overseen_by"])

    def test_nonexistent_schedule(self):
        """Test with non-existent building schedule ID"""
        nonexistent_url = f'/api/jobs/buildings/{uuid4()}/complete-schedule/'
        data = {
            "elevators": [
                self._create_elevator_payload(self.elevators[0].id)
            ]
        }
        response = self.client.post(nonexistent_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_already_completed_schedule(self):
        """Test attempting to complete an already completed schedule"""
        self.building_schedule.status = 'completed'
        self.building_schedule.save()
        
        data = {
            "elevators": [
                self._create_elevator_payload(self.elevators[0].id)
            ]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been completed", response.data["message"])

    def test_elevator_not_in_building(self):
        """Test with elevator that doesn't belong to the building"""
        other_building = BuildingFactory()
        other_elevator = ElevatorFactory(building=other_building)
        
        data = {
            "elevators": [
                self._create_elevator_payload(other_elevator.id)
            ]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_missing_required_fields(self):
        """Test with missing required fields in the request"""
        data = {
            "elevators": [
                {
                    "elevator_id": str(self.elevators[0].id),
                    "condition_report": {
                        "components_checked": self.valid_elevator_data["components_checked"]
                        # Missing 'condition' field
                    },
                    "maintenance_log": {
                        "summary_title": self.valid_elevator_data["summary_title"],
                        "description": self.valid_elevator_data["description"]
                        # Missing 'overseen_by' field
                    }
                }
            ]
        }
    
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    def test_invalid_uuid_format(self):
        """Test with invalid UUID format for elevator ID"""
        data = {
            "elevators": [
                {
                    "elevator_id": "invalid-uuid",
                    "condition_report": {
                        "components_checked": self.valid_elevator_data["components_checked"],
                        "condition": self.valid_elevator_data["condition"]
                    },
                    "maintenance_log": {
                        "summary_title": self.valid_elevator_data["summary_title"],
                        "description": self.valid_elevator_data["description"],
                        "overseen_by": self.valid_elevator_data["overseen_by"]
                    }
                }
            ]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
    
    def test_partial_success(self):
        """Test scenario where some elevators succeed and others fail"""
        other_building = BuildingFactory()
        other_elevator = ElevatorFactory(building=other_building)
        
        data = {
            "elevators": [
                self._create_elevator_payload(self.elevators[0].id),
                self._create_elevator_payload(other_elevator.id)
            ]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        
        # Verify the building schedule wasn't marked as completed
        self.building_schedule.refresh_from_db()
        self.assertEqual(self.building_schedule.status, 'scheduled')

    def test_empty_elevator_list(self):
        """Test with empty elevator list"""
        data = {"elevators": []}
    
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertTrue(any('No elevators provided' in error for error in response.data['errors']))
     

    def test_duplicate_elevator_ids(self):
        """Test with duplicate elevator IDs in the request"""
        data = {
            "elevators": [
                self._create_elevator_payload(self.elevators[0].id),
                self._create_elevator_payload(self.elevators[0].id)
            ]
        }
    
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)
        self.assertTrue(any('Duplicate elevator ID' in error for error in response.data['errors']))
    
        # Verify no records were created due to the duplicate ID error
        self.assertEqual(
            AdHocMaintenanceSchedule.objects.filter(
                elevator=self.elevators[0]
            ).count(),
            0
        ) 
