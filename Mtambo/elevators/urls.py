from django.urls import path
from . views import *

urlpatterns = [
    path('add/', AddElevatorView.as_view(), name='add-elevator'),
    path('', ElevatorListView.as_view(), name='elevator-list'),
    path('<uuid:id>/', ElevatorDetailByIdView.as_view(), name='elevator-detail'),
    path('machine-number/<str:machine_number>/', ElevatorDetailByMachineNumberView.as_view(), name='elevator-detail-by-machine-number'),
    path('<uuid:building_id>/elevator/', ElevatorsInBuildingView.as_view(), name='elevators-in-building'),
    path('<uuid:id>/delete/', DeleteElevatorView.as_view(), name='delete-elevator'),
    path('<uuid:elevator_id>/log-issue/', LogElevatorIssueView.as_view(), name='log-elevator-issue'),
    path('<uuid:elevator_id>/issues/', LoggedElevatorIssuesView.as_view(), name='logged-elevator-issues'),
    path('with_running_schedules/', ElevatorWithRunningSchedulesView.as_view(), name='elevator-with-running-schedules'),
    path('no_running_schedules/', ElevatorWithoutRunningSchedulesView.as_view(), name='elevator-no-running-schedules'),
]

