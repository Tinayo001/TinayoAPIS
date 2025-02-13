from django.urls import URLPattern, path
from .views import *


urlpatterns = [
        path('maintenance-schedules/elevators/<uuid:elevator_id>/create/', CreateRoutineMaintenanceScheduleView.as_view(), name='create-maintenance-schedule'),
        path('maintenance-schedules/elevator/<uuid:elevator_uuid>/create-adhoc/', CreateAdHocMaintenanceScheduleView.as_view(), name='create_ad_hoc_maintenance_schedule'),
        path('maintenance-schedules/<uuid:schedule_id>/complete/', ChangeMaintenanceScheduleToCompletedView.as_view(), name='complete-maintenance-schedule'),
        path("maintenance-schedules/<uuid:schedule_id>/remove/", MaintenanceScheduleDeleteView.as_view(), name="maintenance-schedule-delete"),
        path('maintenance-schedules/elevators/<uuid:elevator_id>/', ElevatorMaintenanceSchedulesView.as_view(), name='elevator-maintenance-schedules'),
        path('maintenance-schedules/technicians/<uuid:technician_id>/', TechnicianMaintenanceSchedulesView.as_view(), name='technician-maintenance-schedules'),
        path('maintenance-schedules/', MaintenanceScheduleListView.as_view(), name='maintenance-schedule-list'),    
        path('maintenance-schedules/maintenance_company/<uuid:company_id>/', MaintenanceCompanyMaintenanceSchedulesView.as_view(), name='maintenance-company-schedules'),
        path('maintenance-schedules/developer/<uuid:developer_id>/', DeveloperMaintenanceSchedulesView.as_view(), name='developer-maintenance-schedules'),
        path('maintenance-schedules/buildings/<uuid:building_id>/', BuildingMaintenanceSchedulesView.as_view(), name='building-maintenance-schedules'),
        path('maintenance-schedules/change-technician/<str:schedule_type>/<uuid:schedule_id>/', ChangeTechnicianView.as_view(), name='change-technician'),
        path('maintenance-schedules/unassigned/', MaintenanceScheduleNullTechnicianFilterView.as_view(), name='unassigned-maintenance-schedules'),
        path('maintenance-schedules/filter/', MaintenanceScheduleFilterView.as_view(), name='maintenance-schedule-filter'),
        path('maintenance-schedules/buildings/<uuid:building_id>/create_building_adhoc/', CreateBuildingAdhocScheduleView.as_view(), name='building-adhoc-schedule-create'),
        path('buildings/<uuid:building_schedule_id>/complete-schedule/', CompleteBuildingScheduleView.as_view(), name='complete-building-schedule'),
        path("maintenance-schedules/maintenance-company/<uuid:company_uuid>/<str:job_status>/", MaintenanceCompanyJobStatusView.as_view(), name="maintenance_company_job_status"),
        path("maintenance-schedules/technician/<uuid:technician_uuid>/<str:job_status>/", TechnicianJobStatusView.as_view(), name="technician_job_status"),
        path('maintenance-schedules/elevator/<uuid:elevator_id>/maintenance-history/', ElevatorMaintenanceHistoryView.as_view(), name='elevator-maintenance-history'),
        path('maintenance-schedules/<uuid:schedule_id>/file-maintenance-log', FileMaintenanceLogView.as_view(), name='file-maintenance-log'),
]

