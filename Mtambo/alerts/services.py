from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
import logging

from .models import Alert, AlertType

logger = logging.getLogger(__name__)


class AlertService:
    """
    Service class for handling all alert-related operations
    """
    
    @classmethod
    def validate_alert_inputs(cls, alert_type, recipient, related_object):
        """
        Validate inputs for alert creation
        """
        if not isinstance(alert_type, str) or alert_type not in AlertType.values:
            raise ValidationError(_("Invalid alert type"))
        
        if not recipient:
            raise ValidationError(_("Recipient is required"))
            
        if not related_object:
            raise ValidationError(_("Related object is required"))
            
        # Validate recipient exists
        if not recipient.__class__.objects.filter(id=recipient.id).exists():
            raise ObjectDoesNotExist(f"Recipient {recipient} does not exist")

        # Validate related_object exists
        if not related_object.__class__.objects.filter(id=related_object.id).exists():
            raise ObjectDoesNotExist(f"Related object {related_object} does not exist")

    @classmethod
    @transaction.atomic
    def create_alert(cls, alert_type, recipient, related_object, message=None):
        """Create an alert with validation and error handling"""
        try:
            # Validate inputs
            cls.validate_alert_inputs(alert_type, recipient, related_object)

            if message is None:
                message = cls.get_default_message(alert_type, related_object)

            alert = Alert.objects.create(
                alert_type=alert_type,
                recipient_type=ContentType.objects.get_for_model(recipient),
                recipient_id=recipient.id,
                content_type=ContentType.objects.get_for_model(related_object),
                object_id=related_object.id,
                message=message
            )
        
            # Verify the alert was actually saved
            try:
                saved_alert = Alert.objects.get(id=alert.id)
                logger.info(
                    f"Alert verified in database: id={saved_alert.id}, "
                    f"type={saved_alert.alert_type}, "
                    f"recipient={saved_alert.recipient}"
                )
            except Alert.DoesNotExist:
                logger.error(f"Alert {alert.id} was created but not found in database!")
                raise Exception("Alert creation failed - could not verify in database")

            logger.info(
                f"Alert created successfully: id={alert.id}, type={alert_type}, "
                f"recipient={recipient}, object={related_object}"
            )
        
            return alert

        except Exception as e:
            logger.error(f"Failed to create alert: {str(e)}", exc_info=True)
            raise 

    @classmethod
    def get_default_message(cls, alert_type, related_object):
        """
        Generate default message based on alert type and related object
        """
        try:
            messages = {
                AlertType.TECHNICIAN_SIGNUP: (
                    f"New technician {related_object.get_full_name()} has signed up "
                    f"under your company"
                ),
                AlertType.ELEVATOR_ASSIGNED: (
                    f"Elevator {related_object.machine_number} has been assigned to you"
                ),
                AlertType.SCHEDULE_ASSIGNED: (
                    f"New maintenance schedule has been assigned for elevator "
                    f"{related_object.elevator.machine_number}"
                ),
                AlertType.LOG_ADDED: (
                    f"New maintenance log added for elevator "
                    f"{related_object.elevator.machine_number}"
                ),
                AlertType.TASK_OVERDUE: (
                    f"Task for elevator {related_object.elevator.machine_number} "
                    f"is overdue"
                ),
                AlertType.TECHNICIAN_UNLINK: (
                    f"Technician {related_object.get_full_name()} has unlinked "
                    f"from your company"
                ),
                AlertType.ELEVATOR_REGISTERED: (
                    f"Elevator {related_object.machine_number} has been registered "
                    f"to {related_object.maintenance_company.company_name}"
                ),
                AlertType.BUILDING_REGISTERED: (
                    f"Building {related_object.name} has been registered in the system"
                )
            }
            return messages.get(alert_type, "New alert")
        except AttributeError as e:
            logger.error(f"Error generating default message: {str(e)}")
            return "New alert"

    @classmethod
    @transaction.atomic
    def create_building_registration_alert(cls, building, company, developer):
        """
        Create alerts for building registration
        """
        try:
            # Create alert for developer
            developer_alert = cls.create_alert(
                alert_type=AlertType.BUILDING_REGISTERED,
                recipient=developer,
                related_object=building,
                message=(
                    f"Your building '{building.name}' has been registered by "
                    f"maintenance company '{company.company_name}'"
                )
            )

            # Create alert for company
            company_alert = cls.create_alert(
                alert_type=AlertType.BUILDING_REGISTERED,
                recipient=company,
                related_object=building,
                message=f"Building '{building.name}' has been successfully registered"
            )

            return developer_alert, company_alert

        except Exception as e:
            logger.error(
                f"Failed to create building registration alerts: building={building}, "
                f"company={company}, developer={developer}, error={str(e)}"
            )
            raise

    @classmethod
    @transaction.atomic
    def create_elevator_registration_alerts(cls, elevators, building, company, developer):
        """
        Create alerts for elevator registration
        """
        try:
            alerts = []
            
            # Alert for developer
            developer_alert = cls.create_alert(
                alert_type=AlertType.ELEVATOR_REGISTERED,
                recipient=developer,
                related_object=building,
                message=(
                    f"{len(elevators)} elevator(s) have been registered to "
                    f"{company.company_name} in building {building.name}"
                )
            )
            alerts.append(developer_alert)

            # Alerts for assigned technicians
            for elevator in elevators:
                if elevator.technician:
                    tech_alert = cls.create_alert(
                        alert_type=AlertType.ELEVATOR_ASSIGNED,
                        recipient=elevator.technician,
                        related_object=elevator,
                        message=(
                            f"New elevator {elevator.machine_number} has been "
                            f"assigned to you in building {building.name}"
                        )
                    )
                    alerts.append(tech_alert)

            # Alert for maintenance company
            company_alert = cls.create_alert(
                alert_type=AlertType.ELEVATOR_REGISTERED,
                recipient=company,
                related_object=building,
                message=(
                    f"{len(elevators)} elevator(s) have been successfully registered "
                    f"in building {building.name}"
                )
            )
            alerts.append(company_alert)

            return alerts

        except Exception as e:
            logger.error(
                f"Failed to create elevator registration alerts: building={building}, "
                f"error={str(e)}"
            )
            raise
