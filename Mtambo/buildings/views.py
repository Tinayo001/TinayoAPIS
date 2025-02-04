from rest_framework import status
from uuid import UUID
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from account.models import User
from developers.models import DeveloperProfile
from .models import Building
from .serializers import BuildingSerializer, AddBuildingRequestSerializer
import uuid
from elevators.models import Elevator

from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from rest_framework.schemas import AutoSchema


class BuildingPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 100

class AddBuildingView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # First, validate the developer_id format
            developer_id = request.data.get('developer_id')
            try:
                developer_uuid = uuid.UUID(str(developer_id))
            except (ValueError, TypeError, AttributeError):
                return Response(
                    {'developer_id': 'Invalid UUID format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Try to fetch the developer
            try:
                developer = DeveloperProfile.objects.get(id=developer_uuid)
            except DeveloperProfile.DoesNotExist:
                return Response(
                    {'error': f'Developer with ID {developer_id} does not exist.'}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # Prepare the building data
            building_data = {
                'developer': developer.id,
                'name': request.data.get('name'),
                'address': request.data.get('address'),
                'contact': request.data.get('contact'),
                'developer_name': developer.developer_name
            }

            # Validate and create the building
            building_serializer = BuildingSerializer(data=building_data)
            if building_serializer.is_valid():
                building = building_serializer.save()
                return Response(building_serializer.data, status=status.HTTP_201_CREATED)
            
            return Response(building_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class ListBuildingsView(APIView):
    permission_classes = [AllowAny]  # Can be updated based on your needs

    def get(self, request):
        """
        Retrieve all buildings from the database with pagination.
        Optimized for large datasets and UUID usage.
        """
        # Pagination setup: Limit results per page and provide page numbers
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Customize this based on your preferences (e.g., 10, 20, etc.)
        
        # Efficient query using select_related to minimize database queries
        buildings = Building.objects.select_related('developer').all()

        # Serialize the data
        serializer = BuildingSerializer(buildings, many=True)

        # Paginate and return the response
        paginated_data = paginator.paginate_queryset(buildings, request)
        return paginator.get_paginated_response(serializer.data)


class GetBuildingDetailsView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, building_id):
        # First validate UUID format before attempting database query
        try:
            # Attempt to convert the building_id to a valid UUID
            uuid_obj = UUID(str(building_id))
        except (ValueError, AttributeError):
            # If conversion fails, it's an invalid UUID format
            return Response(
                {"error": "Invalid UUID format."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            # Now try to fetch the building using the validated UUID
            building = Building.objects.get(id=uuid_obj)
        except Building.DoesNotExist:
            # If the building doesn't exist, return a 404 error
            return Response(
                {"error": "Building not found."}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # If the building is found, return the building details
        serializer = BuildingSerializer(building)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetBuildingsByDeveloperView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, developer_id):
        try:
            # Ensure developer exists
            developer = DeveloperProfile.objects.get(id=developer_id)
        except DeveloperProfile.DoesNotExist:
            return Response({"error": "Developer not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch buildings for the given developer
        buildings = Building.objects.filter(developer=developer)

        if not buildings:
            return Response({"error": "No buildings found for this developer."}, status=status.HTTP_404_NOT_FOUND)

        # Apply pagination
        paginator = BuildingPagination()
        result_page = paginator.paginate_queryset(buildings, request)
        if result_page is not None:
            # If pagination applies
            return paginator.get_paginated_response(BuildingSerializer(result_page, many=True).data)
        
        # If no pagination, just return all the data (for edge cases or default behavior)
        serializer = BuildingSerializer(buildings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

