from django.urls import path
from alerts.views import (
    AlertListView,
    UnreadAlertsView,
    MarkAlertReadView,
    MarkAllAlertsReadView
)

app_name = 'alerts'

urlpatterns = [
    path('', AlertListView.as_view(), name='alert-list'),
    path('unread/', UnreadAlertsView.as_view(), name='unread-alerts'),
    path('<uuid:id>/mark-read/', MarkAlertReadView.as_view(), name='mark-alert-read'),
    path('mark-all-read/', MarkAllAlertsReadView.as_view(), name='mark-all-read'),
]
