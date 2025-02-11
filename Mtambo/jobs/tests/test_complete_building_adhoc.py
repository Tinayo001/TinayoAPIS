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

    def test_successful_completion(self):
        """Test successful completion of building schedule with valid data"""
        data = {
            "elevators": [str(elevator.id) for elevator in self.elevators]
        }

        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.building_schedule.refresh_from_db()
        self.assertEqual(self.building_schedule.status, 'completed')
        
        # Verify creation of related objects
        for elevator in self.elevators:
            # Check AdHocMaintenanceSchedule was created
            self.assertTrue(
                AdHocMaintenanceSchedule.objects.filter(
                    elevator=elevator,
                    status='completed'
                ).exists()
            )
            
            adhoc_schedule = AdHocMaintenanceSchedule.objects.get(
                elevator=elevator,
                status='completed'
            )
            
            # Check condition report was created
            self.assertTrue(
                AdHocElevatorConditionReport.objects.filter(
                    ad_hoc_schedule=adhoc_schedule
                ).exists()
            )
            
            # Check maintenance log was created
            self.assertTrue(
                AdHocMaintenanceLog.objects.filter(
                    ad_hoc_schedule=adhoc_schedule
                ).exists()
            ) 

    def test_nonexistent_schedule(self):
        """Test with non-existent building schedule ID"""
        nonexistent_url = f'/api/jobs/buildings/{uuid4()}/complete-schedule/'
        response = self.client.post(nonexistent_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_already_completed_schedule(self):
        """Test attempting to complete an already completed schedule"""
        self.building_schedule.status = 'completed'
        self.building_schedule.save()
        
        data = {
            "elevators": [
                {
                    "elevator_id": str(self.elevators[0].id),
                    "condition_report": {
                        "components_checked": "All major components",
                        "condition": "Good working condition"
                    },
                    "maintenance_log": {
                        "summary_title": "Regular maintenance",
                        "description": "Completed all checks",
                        "overseen_by": "John Supervisor"
                    }
                }
            ]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_elevator_not_in_building(self):
        """Test with elevator that doesn't belong to the building"""
        other_building = BuildingFactory()
        other_elevator = ElevatorFactory(building=other_building)
        
        data = {
            "elevators": [
                {
                    "elevator_id": str(other_elevator.id),
                    "condition_report": {
                        "components_checked": "All major components",
                        "condition": "Good working condition"
                    },
                    "maintenance_log": {
                        "summary_title": "Regular maintenance",
                        "description": "Completed all checks",
                        "overseen_by": "John Supervisor"
                    }
                }
            ]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('failed_elevators', response.data)

    def test_missing_required_data(self):
        """Test with missing required data in the request"""
        data = {
            "elevators": [str(self.elevators[0].id)]  # Just send the elevator UUID
        }
    
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
        # Verify that default values were used
        adhoc_schedule = AdHocMaintenanceSchedule.objects.get(
            elevator=self.elevators[0],
            status='completed'
        )
    
        # Verify condition report was created with default values
        condition_report = AdHocElevatorConditionReport.objects.get(
            ad_hoc_schedule=adhoc_schedule
        )
        self.assertEqual(condition_report.components_checked, "Default components check - all components normal.")
        self.assertEqual(condition_report.condition, "Good")
    
        # Verify maintenance log was created with default values
        maintenance_log = AdHocMaintenanceLog.objects.get(
            ad_hoc_schedule=adhoc_schedule
        )
        self.assertEqual(maintenance_log.summary_title, "Auto-generated maintenance log")
        self.assertEqual(
            maintenance_log.description, 
            "Maintenance log auto-generated based on building-level schedule completion."
        )
        self.assertEqual(maintenance_log.overseen_by, "System")
    
    def test_partial_success(self):
        """Test scenario where some elevators succeed and others fail"""
        other_building = BuildingFactory()
        other_elevator = ElevatorFactory(building=other_building)
        
        data = {
            "elevators": [
                {
                    "elevator_id": str(self.elevators[0].id),
                    "condition_report": {
                        "components_checked": "All major components",
                        "condition": "Good working condition"
                    },
                    "maintenance_log": {
                        "summary_title": "Regular maintenance",
                        "description": "Completed all checks",
                        "overseen_by": "John Supervisor"
                    }
                },
                {
                    "elevator_id": str(other_elevator.id),  # This should fail
                    "condition_report": {
                        "components_checked": "All major components",
                        "condition": "Good working condition"
                    },
                    "maintenance_log": {
                        "summary_title": "Regular maintenance",
                        "description": "Completed all checks",
                        "overseen_by": "John Supervisor"
                    }
                }
            ]
        }
        
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('failed_elevators', response.data)
        
        # Verify the building schedule wasn't marked as completed
        self.building_schedule.refresh_from_db()
        self.assertEqual(self.building_schedule.status, 'scheduled')
