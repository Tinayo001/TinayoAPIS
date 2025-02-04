from django.urls import path
from .views import *
from .views import DeveloperDetailView, DeveloperDetailByEmailView

urlpatterns = [
    path('<uuid:developer_id>/', DeveloperDetailView.as_view(), name='developer-detail'),
    path('email/<str:developer_email>/', DeveloperDetailByEmailView.as_view(), name='developer-detail-by-email'),
    path('<uuid:developer_uuid>/maintenance/logs/', DeveloperMaintenanceLogApprovalView.as_view(), name='developer-maintenance-log-approval') 
]

