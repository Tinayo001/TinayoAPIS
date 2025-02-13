from django.utils import timezone
import factory
from factory import Faker, SubFactory, Sequence
from factory.django import DjangoModelFactory
from account.models import User
from maintenance_companies.models import MaintenanceCompanyProfile
from technicians.models import TechnicianProfile
from developers.models import DeveloperProfile
from buildings.models import Building
from elevators.models import Elevator
from jobs.models import (
    MaintenanceSchedule, ElevatorConditionReport, ScheduledMaintenanceLog,
    AdHocMaintenanceSchedule, AdHocElevatorConditionReport, AdHocMaintenanceLog,
    BuildingLevelAdhocSchedule, MaintenanceCheck, AdHocMaintenanceTask
)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    first_name = Faker('first_name')
    last_name = Faker('last_name')
    email = Sequence(lambda n: f'user_{n}@example.com')
    phone_number = Sequence(lambda n: f'+1555000{n:04d}')
    account_type = factory.Iterator(['developer', 'maintenance', 'technician'])
    created_at = factory.LazyFunction(timezone.now)
    is_staff = False
    is_superuser = False
    is_active = True


class MaintenanceCompanyProfileFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceCompanyProfile
    
    user = SubFactory(UserFactory, account_type='maintenance')
    company_name = Sequence(lambda n: f'Maintenance Company {n}')
    company_address = Faker('address')
    registration_number = Sequence(lambda n: f'REG{n:05d}')
    specialization = Faker('word')


class TechnicianProfileFactory(DjangoModelFactory):
    class Meta:
        model = TechnicianProfile
    
    user = SubFactory(UserFactory, account_type='technician')
    specialization = Faker('word')
    maintenance_company = SubFactory(MaintenanceCompanyProfileFactory)
    is_approved = True
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)


class DeveloperProfileFactory(DjangoModelFactory):
    class Meta:
        model = DeveloperProfile
    
    user = SubFactory(UserFactory, account_type='developer')
    developer_name = Sequence(lambda n: f'Developer Company {n}')
    address = Faker('address')
    specialization = Faker('word')


class BuildingFactory(DjangoModelFactory):
    class Meta:
        model = Building
    
    name = Sequence(lambda n: f'Building {n}')
    address = Faker('address')
    contact = Sequence(lambda n: f'+1555999{n:04d}')
    developer = SubFactory(DeveloperProfileFactory)


class ElevatorFactory(DjangoModelFactory):
    class Meta:
        model = Elevator
    
    user_name = Sequence(lambda n: f'Elevator {n}')
    controller_type = Faker('word')
    machine_type = factory.Iterator(['gearless', 'geared'])
    building = SubFactory(BuildingFactory)
    machine_number = Sequence(lambda n: f'MACH{n:05d}')
    capacity = Faker('random_int', min=500, max=5000)
    manufacturer = Faker('company')
    installation_date = factory.LazyFunction(lambda: timezone.now().date())
    maintenance_company = SubFactory(MaintenanceCompanyProfileFactory)
    developer = SubFactory(DeveloperProfileFactory)
    technician = SubFactory(TechnicianProfileFactory)


class MaintenanceScheduleFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceSchedule

    elevator = SubFactory(ElevatorFactory)
    technician = SubFactory(TechnicianProfileFactory)
    maintenance_company = SubFactory(MaintenanceCompanyProfileFactory)
    scheduled_date = factory.LazyFunction(timezone.now)
    next_schedule = factory.Iterator(['1_month', '3_months', '6_months', 'set_date'])
    description = Faker('paragraph')
    status = factory.Iterator(['scheduled', 'overdue', 'completed'])


class ElevatorConditionReportFactory(DjangoModelFactory):
    class Meta:
        model = ElevatorConditionReport
    
    maintenance_schedule = SubFactory(MaintenanceScheduleFactory)
    technician = SubFactory(TechnicianProfileFactory)
    date_inspected = factory.LazyFunction(timezone.now)
    alarm_bell = Faker('word')
    noise_during_motion = Faker('word')
    cabin_lights = Faker('word')
    position_indicators = Faker('word')
    hall_lantern_indicators = Faker('word')
    cabin_flooring = Faker('word')
    additional_comments = Faker('sentence')


class ScheduledMaintenanceLogFactory(DjangoModelFactory):
    class Meta:
        model = ScheduledMaintenanceLog
    
    maintenance_schedule = SubFactory(MaintenanceScheduleFactory)
    technician = SubFactory(TechnicianProfileFactory)
    condition_report = SubFactory(ElevatorConditionReportFactory)
    date_completed = factory.LazyFunction(timezone.now)
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


class AdHocMaintenanceScheduleFactory(DjangoModelFactory):
    class Meta:
        model = AdHocMaintenanceSchedule
    
    elevator = SubFactory(ElevatorFactory)
    technician = SubFactory(TechnicianProfileFactory)
    maintenance_company = SubFactory(MaintenanceCompanyProfileFactory)
    scheduled_date = factory.LazyFunction(timezone.now)
    description = Faker('sentence')
    status = factory.Iterator(['scheduled', 'overdue', 'completed'])


class AdHocElevatorConditionReportFactory(DjangoModelFactory):
    class Meta:
        model = AdHocElevatorConditionReport
    
    ad_hoc_schedule = SubFactory(AdHocMaintenanceScheduleFactory)
    technician = SubFactory(TechnicianProfileFactory)
    date_inspected = factory.LazyFunction(timezone.now)
    components_checked = Faker('sentence')
    condition = Faker('sentence')


class AdHocMaintenanceLogFactory(DjangoModelFactory):
    class Meta:
        model = AdHocMaintenanceLog
    
    ad_hoc_schedule = SubFactory(AdHocMaintenanceScheduleFactory)
    technician = SubFactory(TechnicianProfileFactory)
    condition_report = SubFactory(AdHocElevatorConditionReportFactory)
    date_completed = factory.LazyFunction(timezone.now)
    summary_title = Faker('sentence')
    description = Faker('sentence')
    overseen_by = Faker('name')
    approved_by = Faker('name')


class BuildingLevelAdhocScheduleFactory(DjangoModelFactory):
    class Meta:
        model = BuildingLevelAdhocSchedule
    
    building = SubFactory(BuildingFactory)
    technician = SubFactory(TechnicianProfileFactory)
    maintenance_company = SubFactory(MaintenanceCompanyProfileFactory)
    scheduled_date = factory.LazyFunction(timezone.now)
    description = Faker('sentence')
    status = factory.Iterator(['scheduled', 'overdue', 'completed'])


class MaintenanceCheckFactory(DjangoModelFactory):
    class Meta:
        model = MaintenanceCheck
    
    maintenance_schedule = SubFactory(MaintenanceScheduleFactory)
    task_description = Faker('sentence')
    passed = Faker('boolean')
    comments = Faker('sentence')


class AdHocMaintenanceTaskFactory(DjangoModelFactory):
    class Meta:
        model = AdHocMaintenanceTask
    
    description = Faker('sentence')
    created_by = SubFactory(MaintenanceCompanyProfileFactory)
    assigned_to = SubFactory(TechnicianProfileFactory)
    created_at = factory.LazyFunction(timezone.now)
    scheduled_date = factory.LazyFunction(timezone.now)
    completed = Faker('boolean')
    comments = Faker('sentence')
