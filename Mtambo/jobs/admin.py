from django.contrib import admin
from .models import (
    MaintenanceSchedule, ElevatorConditionReport, ScheduledMaintenanceLog,
    AdHocMaintenanceSchedule, AdHocElevatorConditionReport, AdHocMaintenanceLog,
    BuildingLevelAdhocSchedule, MaintenanceCheck, AdHocMaintenanceTask
)

class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('elevator', 'technician', 'maintenance_company', 'scheduled_date', 'status')
    search_fields = ('elevator__user__first_name', 'elevator__user__last_name', 'technician__user__first_name', 'technician__user__last_name')
    list_filter = ('status', 'next_schedule')
    date_hierarchy = 'scheduled_date'
    ordering = ('scheduled_date',)
    readonly_fields = ('id',)

class ElevatorConditionReportAdmin(admin.ModelAdmin):
    list_display = ('maintenance_schedule', 'technician', 'date_inspected')
    search_fields = ('maintenance_schedule__elevator__user__first_name', 'maintenance_schedule__elevator__user__last_name', 'technician__user__first_name', 'technician__user__last_name')
    list_filter = ('date_inspected',)
    readonly_fields = ('id',)

class ScheduledMaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('maintenance_schedule', 'technician', 'date_completed', 'check_machine_gear', 
                    'check_machine_brake', 'check_controller_connections', 'observe_operation')
    search_fields = ('maintenance_schedule__elevator__user__first_name', 
                    'maintenance_schedule__elevator__user__last_name', 
                    'technician__user__first_name', 
                    'technician__user__last_name')
    list_filter = ('date_completed', 'check_machine_gear', 'check_machine_brake', 
                  'check_controller_connections', 'observe_operation')
    readonly_fields = ('id',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('maintenance_schedule', 'technician', 'condition_report', 'date_completed')
        }),
        ('Checklist', {
            'fields': (
                'check_machine_gear',
                'check_machine_brake',
                'check_controller_connections',
                'blow_dust_from_controller',
                'clean_machine_room',
                'clean_guide_rails',
                'observe_operation'
            )
        }),
        ('Additional Information', {
            'fields': ('description', 'overseen_by', 'approved_by')
        })
    )

class AdHocMaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display = ('elevator', 'technician', 'maintenance_company', 'scheduled_date', 'status')
    search_fields = ('elevator__user__first_name', 'elevator__user__last_name', 'technician__user__first_name', 'technician__user__last_name')
    list_filter = ('status',)
    date_hierarchy = 'scheduled_date'
    ordering = ('scheduled_date',)
    readonly_fields = ('id',)

class AdHocElevatorConditionReportAdmin(admin.ModelAdmin):
    list_display = ('ad_hoc_schedule', 'technician', 'date_inspected', 'condition')
    search_fields = ('ad_hoc_schedule__elevator__user__first_name', 'ad_hoc_schedule__elevator__user__last_name', 'technician__user__first_name', 'technician__user__last_name')
    list_filter = ('date_inspected',)
    readonly_fields = ('id',)

class AdHocMaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('ad_hoc_schedule', 'technician', 'date_completed', 'summary_title')
    search_fields = ('ad_hoc_schedule__elevator__user__first_name', 'ad_hoc_schedule__elevator__user__last_name', 'technician__user__first_name', 'technician__user__last_name')
    list_filter = ('date_completed',)
    readonly_fields = ('id',)

class BuildingLevelAdhocScheduleAdmin(admin.ModelAdmin):
    list_display = ('building', 'technician', 'maintenance_company', 'scheduled_date', 'status')
    search_fields = ('building__name', 'technician__user__first_name', 'technician__user__last_name')
    list_filter = ('status',)
    date_hierarchy = 'scheduled_date'
    ordering = ('scheduled_date',)
    readonly_fields = ('id',)

class MaintenanceCheckAdmin(admin.ModelAdmin):
    list_display = ('maintenance_schedule', 'task_description', 'passed', 'comments')
    search_fields = ('maintenance_schedule__elevator__user__first_name', 'maintenance_schedule__elevator__user__last_name', 'task_description')
    list_filter = ('passed',)
    readonly_fields = ('id',)

class AdHocMaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'assigned_to', 'scheduled_date', 'completed', 'comments')
    search_fields = ('created_by__company_name', 'assigned_to__user__first_name', 'assigned_to__user__last_name', 'description')
    list_filter = ('completed',)
    date_hierarchy = 'scheduled_date'
    ordering = ('scheduled_date',)
    readonly_fields = ('id',)

# Registering models with the admin site
admin.site.register(MaintenanceSchedule, MaintenanceScheduleAdmin)
admin.site.register(ElevatorConditionReport, ElevatorConditionReportAdmin)
admin.site.register(ScheduledMaintenanceLog, ScheduledMaintenanceLogAdmin)
admin.site.register(AdHocMaintenanceSchedule, AdHocMaintenanceScheduleAdmin)
admin.site.register(AdHocElevatorConditionReport, AdHocElevatorConditionReportAdmin)
admin.site.register(AdHocMaintenanceLog, AdHocMaintenanceLogAdmin)
admin.site.register(BuildingLevelAdhocSchedule, BuildingLevelAdhocScheduleAdmin)
admin.site.register(MaintenanceCheck, MaintenanceCheckAdmin)
admin.site.register(AdHocMaintenanceTask, AdHocMaintenanceTaskAdmin)

