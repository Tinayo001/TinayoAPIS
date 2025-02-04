from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from .models import TechnicianProfile
from account.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny
from .serializers import TechnicianProfileSerializer ,TechnicianListSerializer, TechnicianDetailSerializer, TechnicianSpecializationSerializer
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from uuid import UUID
from drf_yasg import openapi
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email


# View to list all technicians
class TechnicianListView(generics.ListAPIView):
    """
    View to list all technicians associated with a specific maintenance company.
    """
    serializer_class = TechnicianListSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(tags=['Technician List'])
    def get_queryset(self):
        company_uuid = self.kwargs.get('company_uuid')

        if company_uuid:
            try:
                # Only convert string to UUID if it's not already a UUID
                if not isinstance(company_uuid, UUID):
                    company_uuid = UUID(str(company_uuid))
                return TechnicianProfile.objects.filter(maintenance_company_id=company_uuid)
            except ValueError:
                # Handle invalid UUID format
                raise NotFound(detail="Invalid company UUID format")
        return TechnicianProfile.objects.all()

# View to list all technicians by specialization
class TechnicianListBySpecializationView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TechnicianSpecializationSerializer

    @swagger_auto_schema(tags=['Technician List by Specialization'])
    def get_queryset(self):
        specialization = self.kwargs['specialization']
        return TechnicianProfile.objects.filter(specialization=specialization)


# View to get a specific technician's details (using UUID)
class TechnicianDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = TechnicianProfile.objects.all()
    serializer_class = TechnicianDetailSerializer
    lookup_field = 'id'  # Use UUID field for lookup


    @swagger_auto_schema(tags=['Technician Details'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# View for unlinked technicians
class UnlinkTechnicianFromCompanyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        technician_id = kwargs.get('id')
        
        if not technician_id:
            return Response(
                {"error": "No technician ID provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        technician = get_object_or_404(Technician, id=technician_id)
        
        # Check if the authenticated user's company matches the technician's company
        if technician.maintenance_company != request.user.company:
            raise PermissionDenied("You do not have permission to unlink this technician.")
        
        if not technician.maintenance_company:
            return Response(
                {"error": "Technician is not linked to any maintenance company."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        technician.maintenance_company = None
        technician.is_approved = False
        technician.save()
        
        return Response(
            {"message": "Technician successfully unlinked from maintenance company."},
            status=status.HTTP_200_OK,
        )


# View for unlinked technicians by specialization
class UnlinkedTechniciansBySpecializationView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = TechnicianListSerializer

    @swagger_auto_schema(tags=['Unlinked Technicians by Specialization'])
    def get_queryset(self):
        specialization = self.kwargs.get('specialization')
        if specialization:
            return TechnicianProfile.objects.filter(maintenance_company__isnull=True, specialization=specialization)
        return TechnicianProfile.objects.filter(maintenance_company__isnull=True)

    def get(self, request, *args, **kwargs):
        technicians = self.get_queryset()
        if not technicians.exists():
            return Response({"message": "No unlinked technicians found for this specialization."}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(technicians, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# View to get technician details by email (uses UUID for related fields)
class TechnicianDetailByEmailView(APIView):
    permission_classes = [AllowAny]
    serializer_class = TechnicianDetailSerializer

    @swagger_auto_schema(tags=['Technician Details by Email'])
    def get(self, request, technician_email, *args, **kwargs):
        # Validate email format
        try:
            validate_email(technician_email)
        except DjangoValidationError:
            return Response(
                {"error": "Invalid email format."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retrieve the User and Technician profile by email
        try:
            user = User.objects.get(email=technician_email)
        except User.DoesNotExist:
            raise NotFound(detail="User with this email not found.")
        
        try:
            technician = TechnicianProfile.objects.get(user=user)
        except TechnicianProfile.DoesNotExist:
            raise NotFound(detail="User has no technician profile associated.")

        # Create a custom response data structure to match test expectations
        technician_data = {
            'id': str(technician.id),
            'technician_name': f"{user.first_name} {user.last_name}",
            'specialization': technician.specialization,
            'maintenance_company': technician.maintenance_company.id if technician.maintenance_company else None,
            'maintenance_company_name': str(technician.maintenance_company) if technician.maintenance_company else None,
            'email': user.email,
            'phone_number': user.phone_number
        }
        
        return Response({"technician": technician_data}, status=status.HTTP_200_OK)
