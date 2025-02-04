from django.urls import path, re_path
from . views import *

urlpatterns = [
    path('list-buildings/', ListBuildingsView.as_view(), name='list_buildings'),
    path('add-building/', AddBuildingView.as_view(), name='add-building'),
    path('<uuid:building_id>/', GetBuildingDetailsView.as_view(), name='get_building_details'),
    path('developer/<uuid:developer_id>/buildings/', GetBuildingsByDeveloperView.as_view(), name='get_buildings_by_developer'),

]

