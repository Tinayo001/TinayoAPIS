from django.urls import path
from .views import *
from .views import RemoveTechnicianFromCompanyView
from django.urls import re_path
from .views import ElevatorDetailView

app_name = 'maintenance_companies'

urlpatterns = [
    path('', MaintenanceCompanyListView.as_view(), name='maintenance_company_list'),
    path('<uuid:uuid_id>/', MaintenanceCompanyDetailView.as_view(), name='maintenance-company-detail'),
    path('<uuid:company_id>/technicians/pending/', 
         ListPendingTechniciansView.as_view(), 
         name='list-pending-technicians'),
    path('technicians/<uuid:technician_id>/approve/', 
         CompanyAddTechnicianView.as_view(), 
         name='company-add-technician'),
    path('maintenance_companies/<uuid:uuid_id>/', 
         UpdateMaintenanceCompanyView.as_view(), 
         name='update-maintenance-company'),
    path('specialization/<str:specialization>/', MaintenanceCompanyBySpecializationView.as_view(), name='specialization-list'),
    path('specialization/', MaintenanceCompanyBySpecializationView.as_view(), name='specialization-list-empty'),
    path('email/<str:email>/', MaintenanceCompanyByEmailView.as_view(), name='maintenance-company-by-email'),
    path('<uuid:maintenance_company_id>/technicians/<uuid:technician_id>/remove/', 
         RemoveTechnicianFromCompanyView.as_view(), 
        name='remove_technician_from_company'),
    path('<uuid:uuid_id>/technicians/', MaintenanceCompanyTechniciansView.as_view(), name='technicians-list'),
    path('add-building/<uuid:company_uuid>/', AddBuildingView.as_view(), name='add_building'),
    path('<uuid:company_id>/buildings/', BuildingListView.as_view(), name='building-list'),
    path('<uuid:company_id>/buildings/<uuid:building_id>/', BuildingDetailView.as_view(), name='building-detail'),
    path('developers/<uuid:company_id>/', DevelopersUnderCompanyView.as_view(), name='developers-under-company'),
    path('developer/<uuid:company_id>/detail/<uuid:developer_id>/', DeveloperDetailUnderCompanyView.as_view(), name='developer-detail-under-company'),
    path('buildings/<str:company_id>/developer/<str:developer_id>/', BuildingsUnderDeveloperView.as_view()),
    path('elevators/<uuid:company_id>/', ElevatorsUnderCompanyView.as_view(), name='elevators-under-company'),
    path('elevators/<uuid:company_id>/<uuid:building_id>/', ElevatorsInBuildingView.as_view(), name='elevators-in-building'),
    path(
        'elevators/<uuid:company_id>/<uuid:elevator_id>/',
        ElevatorDetailView.as_view(),
        name='elevator-detail'
    ),
    path(
        'elevators/<uuid:company_id>/<str:machine_number>/',
        ElevatorDetailByMachineNumberView.as_view(),
        name='elevator-detail-by-machine-number'
    ),
    path(
        'elevators/<uuid:company_id>/',
        ElevatorDetailByMachineNumberView.as_view(),
        name='elevator-detail-by-machine-number-no-machine'
    ),
    path('<uuid:company_uuid>/technicians/<uuid:technician_uuid>/', TechnicianDetailForCompanyView.as_view(), name='technician-detail-for-company'),
    path('add-elevator/<uuid:company_uuid>/<uuid:building_uuid>/', AddElevatorToBuildingView.as_view(), name='add_elevator_to_building'),
    path('elevators/technician/<uuid:company_id>/<uuid:technician_id>/', ElevatorsUnderTechnicianView.as_view(), name='elevators-under-technician'),
    path('<uuid:company_id>/technicians/<uuid:technician_id>/buildings/', BuildingsUnderTechnicianView.as_view(), name='buildings-under-technician'),
    path('<uuid:company_uuid>/buildings/<uuid:building_uuid>/update-technician/', 
         UpdateTechnicianOnBuildingsView.as_view(), 
         name='update-technician-on-buildings'),
    path('<uuid:company_uuid>/elevators/<uuid:elevator_uuid>/update-technician/', 
         UpdateTechnicianOnElevatorView.as_view(), 
         name='update-technician-on-elevator'),
    path(
        'remove-maintenance-from-elevators/<uuid:company_id>/<uuid:building_id>/',
        RemoveMaintenanceFromBuildingElevatorsView.as_view(),
        name='remove-maintenance-from-elevators'
    ),
    path(
        'remove-maintenance-from-developer-elevators/<uuid:company_id>/<uuid:developer_id>/',
        RemoveMaintenanceFromDeveloperElevatorsView.as_view(),
        name='remove-maintenance-from-developer-elevators'
    ),

]

