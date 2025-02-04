from django.http import Http404
from rest_framework.generics import RetrieveAPIView 
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.generics import UpdateAPIView
from rest_framework.exceptions import NotFound
from rest_framework.generics import DestroyAPIView
from .models import Elevator
from buildings.models import Building
from .serializers import ElevatorSerializer
from .serializers import ElevatorCreateSerializer
import logging
import uuid
from rest_framework.permissions import IsAuthenticated
from .services.elevator_service import ElevatorService
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter


from rest_framework.generics import ListAPIView

logger = logging.getLogger(__name__)

class AddElevatorView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=ElevatorCreateSerializer,
        operation_description="Add a new elevator with details.",
        responses={
            201: openapi.Response(
                description="Elevator created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                        'user_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'machine_number': openapi.Schema(type=openapi.TYPE_STRING),
                        'capacity': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'manufacturer': openapi.Schema(type=openapi.TYPE_STRING),
                        'installation_date': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                        'building': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID),
                        'technician': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_UUID, nullable=True),
                    }
                )
            ),
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error"
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Handle POST request to create a new elevator.
        """
        serializer = ElevatorCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                elevator = ElevatorService.create_elevator(serializer.validated_data)
                return Response(
                    {
                        "id": str(elevator.id),
                        "user_name": elevator.user_name,
                        "machine_number": elevator.machine_number,
                        "capacity": elevator.capacity,
                        "manufacturer": elevator.manufacturer,
                        "installation_date": elevator.installation_date.isoformat(),
                        "building": str(elevator.building.id),
                        "technician": str(elevator.technician.id) if elevator.technician else None,
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ElevatorListView(ListAPIView):
    """
    API view to list all elevators with pagination, filtering, and sorting.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed
    queryset = Elevator.objects.all()
    serializer_class = ElevatorSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['building', 'machine_type', 'manufacturer']  # Add fields to filter by
    ordering_fields = ['installation_date', 'capacity']  # Add fields to sort by
    ordering = ['-installation_date']  # Default ordering

    @swagger_auto_schema(
        operation_description="Retrieve a list of all elevators with optional filtering and sorting.",
        manual_parameters=[
            openapi.Parameter(
                name='building',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by building UUID.",
            ),
            openapi.Parameter(
                name='machine_type',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by machine type (e.g., 'gearless', 'geared').",
            ),
            openapi.Parameter(
                name='manufacturer',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by manufacturer name.",
            ),
            openapi.Parameter(
                name='ordering',
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Sort by fields (e.g., 'installation_date', '-capacity').",
            ),
        ],
        responses={
            200: openapi.Response(
                description="List of elevators retrieved successfully.",
                schema=ElevatorSerializer(many=True),
            ),
            500: "Internal Server Error",
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ElevatorDetailByIdView(RetrieveAPIView):
    """
    Retrieve a specific elevator by its ID.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed
    queryset = Elevator.objects.all()
    serializer_class = ElevatorSerializer
    lookup_field = 'id'  # Match the URL keyword argument

    @swagger_auto_schema(
        operation_description="Retrieve a specific elevator by its ID.",
        responses={
            200: openapi.Response(
                description="Elevator retrieved successfully.",
                schema=ElevatorSerializer,
            ),
            404: "Elevator not found.",
            500: "Internal Server Error",
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve an elevator by its ID.
        """
        try:
            elevator_id = kwargs['id']
            logger.info(f"Attempting to retrieve elevator with ID: {elevator_id}")
            return super().get(request, *args, **kwargs)
        except Http404:
            logger.error(f"Elevator with ID {elevator_id} not found.")
            return Response(
                {"detail": "Elevator not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving elevator: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ElevatorDetailByMachineNumberView(RetrieveAPIView):
    """
    Retrieve a specific elevator by its machine number.
    """
    permission_classes = [AllowAny]  # Allow any user to access this endpoint
    serializer_class = ElevatorSerializer
    lookup_field = 'machine_number'  # Use machine_number for lookup

    def get_object(self):
        """
        Retrieve the elevator by its machine number.
        """
        machine_number = self.kwargs['machine_number']
        logger.info(f"Attempting to retrieve elevator with machine number: {machine_number}")
        return get_object_or_404(Elevator, machine_number=machine_number)

    @swagger_auto_schema(
        operation_description="Retrieve a specific elevator by its machine number.",
        responses={
            200: openapi.Response(
                description="Elevator retrieved successfully.",
                schema=ElevatorSerializer,
            ),
            404: "Elevator not found.",
            500: "Internal Server Error",
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Handle GET request to retrieve an elevator by its machine number.
        """
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            logger.error(f"Elevator with machine number {self.kwargs['machine_number']} not found.")
            return Response(
                {"detail": "Elevator not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving elevator: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ElevatorsInBuildingView(APIView):
    """
    Get all elevators in a specific building identified by building_id.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed

    @swagger_auto_schema(
        operation_description="Retrieve all elevators in a specific building.",
        responses={
            200: openapi.Response(
                description="Elevators retrieved successfully.",
                schema=ElevatorSerializer(many=True),
            ),
            404: "Building not found or no elevators found for this building.",
        }
    )
    def get(self, request, building_id, *args, **kwargs):
        """
        Handle GET request to retrieve all elevators in a building.
        """
        try:
            # Retrieve the building by its UUID
            building = get_object_or_404(Building, id=building_id)
            logger.info(f"Retrieving elevators for building ID: {building_id}")

            # Get all elevators related to this building
            elevators = building.elevators.all()

            # Check if there are no elevators for the given building
            if not elevators.exists():
                logger.warning(f"No elevators found for building ID: {building_id}")
                return Response(
                    {"detail": "No elevators found for this building."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Serialize the elevator data
            serializer = ElevatorSerializer(elevators, many=True)

            # Return the serialized data in the response
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Http404:
            logger.error(f"Building with ID {building_id} not found.")
            return Response(
                {"detail": "Building not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error retrieving elevators for building ID {building_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class DeleteElevatorView(DestroyAPIView):
    """
    Delete a specific elevator by its ID.
    """
    permission_classes = [AllowAny]  # Adjust permissions as needed
    queryset = Elevator.objects.all()
    serializer_class = ElevatorSerializer
    lookup_field = 'id'  # Use 'id' as the lookup field

    @swagger_auto_schema(
        operation_description="Delete a specific elevator by its ID.",
        responses={
            204: openapi.Response(
                description="Elevator deleted successfully.",
            ),
            404: "Elevator not found.",
            500: "Internal Server Error",
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Handle DELETE request to delete an elevator by its ID.
        """
        try:
            elevator_id = self.kwargs['id']
            logger.info(f"Attempting to delete elevator with ID: {elevator_id}")
            return super().delete(request, *args, **kwargs)
        except Http404:
            logger.error(f"Elevator with ID {elevator_id} not found.")
            return Response(
                {"detail": "Elevator not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error deleting elevator with ID {elevator_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": "An internal server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


