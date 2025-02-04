from django.urls import path
from . views import *

urlpatterns = [
    path('add/', AddElevatorView.as_view(), name='add-elevator'),
    path('', ElevatorListView.as_view(), name='elevator-list'),
    path('<uuid:id>/', ElevatorDetailByIdView.as_view(), name='elevator-detail'),
    path('machine-number/<str:machine_number>/', ElevatorDetailByMachineNumberView.as_view(), name='elevator-detail-by-machine-number'),
    path('<uuid:building_id>/elevators/', ElevatorsInBuildingView.as_view(), name='elevators-in-building'),
    path('<uuid:id>/delete/', DeleteElevatorView.as_view(), name='delete-elevator'),
]

