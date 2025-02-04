from django.shortcuts import get_object_or_404
from elevators.models import Elevator
from buildings.models import Building
from technicians.models import TechnicianProfile

class ElevatorService:
    @staticmethod
    def create_elevator(validated_data):
        """
        Create a new elevator instance.
        """
        # Extract related object IDs
        building_id = validated_data.pop('building')
        technician_id = validated_data.pop('technician', None)

        # Fetch related objects
        building = get_object_or_404(Building, id=building_id)
        technician = None
        if technician_id:
            technician = get_object_or_404(TechnicianProfile, id=technician_id)

        # Create the elevator
        elevator = Elevator.objects.create(
            building=building,
            technician=technician,
            **validated_data
        )
        return elevator
