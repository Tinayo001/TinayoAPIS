from django.urls import path
from .views import *

urlpatterns = [
        path('register/', BrokerRegistrationView.as_view(), name='broker-register'),
        path('', BrokerListView.as_view(), name='broker-list'),
        path('broker/<uuid:broker_id>/maintenance-companies/', MaintenanceCompaniesListView.as_view(), name='maintenance-companies-list'),    
]
