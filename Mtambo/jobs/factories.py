import factory
from factory import Faker,  SubFactory
from factory.django import DjangoModelFactory
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from developers.models import DeveloperProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import MaintenanceSchedule, ElevatorConditionReport, ScheduledMaintenanceLog, AdHocMaintenanceSchedule, AdHocElevatorConditionReport, AdHocMaintenanceLog, BuildingLevelAdhocSchedule, MaintenanceCheck, AdHocMaintenanceTask


# Factory for User model
class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Faker('email')
    phone_number = Faker('phone_number')
    account_type = Faker('random_element', elements=['developer', 'maintenance', 'technician'])
    created_at = Faker('date_time_this_decade')
    is_staff = Faker('boolean')
    is_superuser = Faker('boolean')
    is_active = True


# Factory for MaintenanceCompanyProfile model
class MaintenanceCompanyProfileFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceCompanyProfile
    
    user = factory.SubFactory(UserFactory)
    company_name = Faker('company')
    company_address = Faker('address')
    registration_number = Faker('uuid4')
    specialization = Faker('word')


# Factory for TechnicianProfile model
class TechnicianProfileFactory(DjangoModelFactory):
    class Meta:
        model = TechnicianProfile
    
    user = factory.SubFactory(UserFactory)
    specialization = Faker('word')
    maintenance_company = factory.SubFactory(MaintenanceCompanyProfileFactory)
    is_approved = True
    created_at = Faker('date_this_decade')
    updated_at = Faker('date_this_decade')


# Factory for DeveloperProfile model
class DeveloperProfileFactory(DjangoModelFactory):
    class Meta:
        model = DeveloperProfile
    
    user = factory.SubFactory(UserFactory)
    developer_name = Faker('company')
    address = Faker('address')
    specialization = Faker('word')


# Factory for Building model
class BuildingFactory(DjangoModelFactory):
    class Meta:
        model = Building
    
    name = Faker('company')
    address = Faker('address')
    contact = Faker('phone_number')
    developer = factory.SubFactory(DeveloperProfileFactory)


# Factory for Elevator model
class ElevatorFactory(DjangoModelFactory):
    class Meta:
        model = Elevator
    
    user_name = Faker('word')
    controller_type = Faker('word')
    machine_type = Faker('random_element', elements=['gearless', 'geared'])
    building = factory.SubFactory(BuildingFactory)
    machine_number = Faker('uuid4')
    capacity = Faker('random_int', min=500, max=5000)
    manufacturer = Faker('company')
    installation_date = Faker('date_this_decade')
    maintenance_company = SubFactory(MaintenanceCompanyProfileFactory)
    developer = factory.SubFactory(DeveloperProfileFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)


# Factory for MaintenanceSchedule model
class MaintenanceScheduleFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceSchedule
    
    elevator = factory.SubFactory(ElevatorFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)
    maintenance_company = factory.SubFactory(MaintenanceCompanyProfileFactory)
    scheduled_date = factory.Faker('date_this_decade')
    next_schedule = Faker('random_element', elements=['1_month', '3_months', '6_months', 'set_date'])
    description = Faker('sentence')
    status = Faker('random_element', elements=['scheduled', 'overdue', 'completed'])


# Factory for ElevatorConditionReport model
class ElevatorConditionReportFactory(DjangoModelFactory):
    class Meta:
        model = ElevatorConditionReport
    
    maintenance_schedule = factory.SubFactory(MaintenanceScheduleFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)
    date_inspected = Faker('date_this_decade')
    alarm_bell = Faker('word')
    noise_during_motion = Faker('word')
    cabin_lights = Faker('word')
    position_indicators = Faker('word')
    hall_lantern_indicators = Faker('word')
    cabin_flooring = Faker('word')
    additional_comments = Faker('sentence')


# Factory for ScheduledMaintenanceLog model
class ScheduledMaintenanceLogFactory(DjangoModelFactory):
    class Meta:
        model = ScheduledMaintenanceLog
    
    maintenance_schedule = factory.SubFactory(MaintenanceScheduleFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)
    condition_report = factory.SubFactory(ElevatorConditionReportFactory)
    date_completed = Faker('date_this_decade')
    check_machine_gear = Faker('boolean')
    check_machine_brake = Faker('boolean')
    check_controller_connections = Faker('boolean')
    blow_dust_from_controller = Faker('boolean')
    clean_machine_room = Faker('boolean')
    clean_guide_rails = Faker('boolean')
    observe_operation = Faker('boolean')
    description = Faker('sentence')
    overseen_by = Faker('name')
    approved_by = Faker('name')


# Factory for AdHocMaintenanceSchedule model
class AdHocMaintenanceScheduleFactory(DjangoModelFactory):
    class Meta:
        model = AdHocMaintenanceSchedule
    
    elevator = factory.SubFactory(ElevatorFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)
    maintenance_company = factory.SubFactory(MaintenanceCompanyProfileFactory)
    scheduled_date = Faker('date_this_decade')
    description = Faker('sentence')
    status = Faker('random_element', elements=['scheduled', 'overdue', 'completed'])


# Factory for AdHocElevatorConditionReport model
class AdHocElevatorConditionReportFactory(DjangoModelFactory):
    class Meta:
        model = AdHocElevatorConditionReport
    
    ad_hoc_schedule = factory.SubFactory(AdHocMaintenanceScheduleFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)
    date_inspected = Faker('date_this_decade')
    components_checked = Faker('sentence')
    condition = Faker('sentence')


# Factory for AdHocMaintenanceLog model
class AdHocMaintenanceLogFactory(DjangoModelFactory):
    class Meta:
        model = AdHocMaintenanceLog
    
    ad_hoc_schedule = factory.SubFactory(AdHocMaintenanceScheduleFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)
    condition_report = factory.SubFactory(AdHocElevatorConditionReportFactory)
    date_completed = Faker('date_this_decade')
    summary_title = Faker('sentence')
    description = Faker('sentence')
    overseen_by = Faker('name')
    approved_by = Faker('name')


# Factory for BuildingLevelAdhocSchedule model
class BuildingLevelAdhocScheduleFactory(DjangoModelFactory):
    class Meta:
        model = BuildingLevelAdhocSchedule
    
    building = factory.SubFactory(BuildingFactory)
    technician = factory.SubFactory(TechnicianProfileFactory)
    maintenance_company = factory.SubFactory(MaintenanceCompanyProfileFactory)
    scheduled_date = Faker('date_this_decade')
    description = Faker('sentence')
    status = Faker('random_element', elements=['scheduled', 'overdue', 'completed'])


# Factory for MaintenanceCheck model
class MaintenanceCheckFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceCheck
    
    maintenance_schedule = factory.SubFactory(MaintenanceScheduleFactory)
    task_description = Faker('sentence')
    passed = Faker('boolean')
    comments = Faker('sentence')


# Factory for AdHocMaintenanceTask model
class AdHocMaintenanceTaskFactory(DjangoModelFactory):
    class Meta:
        model = AdHocMaintenanceTask
    
    description = Faker('sentence')
    created_by = factory.SubFactory(MaintenanceCompanyProfileFactory)
    assigned_to = factory.SubFactory(TechnicianProfileFactory)
    created_at = Faker('date_this_decade')
    scheduled_date = Faker('date_this_decade')
    completed = Faker('boolean')
    comments = Faker('sentence')

