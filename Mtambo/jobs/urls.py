from django.urls import URLPattern, path
from .views import *


urlpatterns = [
        path('elevators/<uuid:elevator_id>/maintenance-schedules/create/', CreateRoutineMaintenanceScheduleView.as_view(), name='create-maintenance-schedule'),
        path('elevator/<uuid:elevator_uuid>/maintenance/', CreateAdHocMaintenanceScheduleView.as_view(), name='create_ad_hoc_maintenance_schedule'),
        path('maintenance-schedule/<uuid:schedule_id>/complete/', ChangeMaintenanceScheduleToCompletedView.as_view(), name='complete-maintenance-schedule'),
        path("maintenance-schedules/<uuid:schedule_id>/delete/", MaintenanceScheduleDeleteView.as_view(), name="maintenance-schedule-delete"),
        path('elevators/<uuid:elevator_id>/maintenance-schedules/list/', ElevatorMaintenanceSchedulesView.as_view(), name='elevator-maintenance-schedules'),
        path('technicians/<uuid:technician_id>/maintenance-schedules/', TechnicianMaintenanceSchedulesView.as_view(), name='technician-maintenance-schedules'),
        path('maintenance-schedules/', MaintenanceScheduleListView.as_view(), name='maintenance-schedule-list'),    
        path('maintenance-schedules/<uuid:company_id>/', MaintenanceCompanyMaintenanceSchedulesView.as_view(), name='maintenance-company-schedules'),
        path('developer/<uuid:developer_id>/maintenance-schedules/', DeveloperMaintenanceSchedulesView.as_view(), name='developer-maintenance-schedules'),
        path('buildings/<uuid:building_id>/maintenance-schedules/', BuildingMaintenanceSchedulesView.as_view(), name='building-maintenance-schedules'),
        path('change-technician/<str:schedule_type>/<uuid:schedule_id>/', ChangeTechnicianView.as_view(), name='change-technician'),
        path('maintenance-schedules/unassigned/', MaintenanceScheduleNullTechnicianFilterView.as_view(), name='unassigned-maintenance-schedules'),
        path('maintenance-schedules/filter/', MaintenanceScheduleFilterView.as_view(), name='maintenance-schedule-filter'),
        path('buildings/<uuid:building_id>/create-adhoc-schedule/', CreateBuildingAdhocScheduleView.as_view(), name='building-adhoc-schedule-create'),
        path('buildings/<uuid:building_schedule_id>/complete-schedule/', CompleteBuildingScheduleView.as_view(), name='complete-building-schedule'),
        path("maintenance-company/<uuid:company_uuid>/jobs/<str:job_status>/", MaintenanceCompanyJobStatusView.as_view(), name="maintenance_company_job_status"),
        path("technician/<uuid:technician_uuid>/jobs/<str:job_status>/", TechnicianJobStatusView.as_view(), name="technician_job_status"),
        path('elevator/<uuid:elevator_id>/maintenance-history/', ElevatorMaintenanceHistoryView.as_view(), name='elevator-maintenance-history'),
        path('maintenance-logs/<uuid:schedule_id>/', FileMaintenanceLogView.as_view(), name='file-maintenance-log'),
]

