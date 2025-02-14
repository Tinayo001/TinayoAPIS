from django.urls import path,include
from account.views import SignUpView, LoginView, SpecializationListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    # Endpoint to register a new user (Sign Up)
    # POST /api/signup/
    # This endpoint allows a user to sign up based on their account type (developer, maintenance, technician).
    # The request body will contain the user's personal information and additional fields depending on the account type.
    # Example Request Body for a User:
    # {
    #   'email': 'maintenance@example.com',
    #   'password': 'password123',
    #   'first_name': 'John',
    #   'last_name': 'Doe',
    #   'phone_number': '1234567890',
    #   "account_type": "maintenance_company",
    #    }
    # Example Request Body for a Developer:
    # {
    #     "first_name": "John",
    #     "last_name": "Doe",
    #     "email": "john.doe@example.com",
    #     "phone_number": "1234567890",
    #     "password": "password123",
    #     "account_type": "developer",
    #     "developer_name": "John's Dev Services",
    #     "address": "123 Developer St, Dev City"
    # }
    #
    # Example Request Body for a Maintenance Company:
    # {
    #     "first_name": "Jane",
    #     "last_name": "Smith",
    #     "email": "jane.smith@example.com",
    #     "phone_number": "9876543210",
    #     "password": "password123",
    #     "account_type": "maintenance",
    #     "company_name": "Smith Elevators Co.",
    #     "company_address": "456 Elevator Ave, Citytown",
    #     "company_registration_number": "REG123456",
    #     "specialization": HVAC
    # }
    #
    # Example Request Body for a Technician:
    # {
    #     "first_name": "Jake",
    #     "last_name": "Williams",
    #     "email": "jake.williams@example.com",
    #     "phone_number": "1122334455",
    #     "password": "password123",
    #     "account_type": "technician",
    #     "specialization": Elevators,  # ID of the specialization (e.g., Elevators)
    #     "maintenance_company_id": 11  # ID of the maintenance company (e.g., Smith Elevators Co.)
    # }
    path('signup/', SignUpView.as_view(), name='signup'),

    # Endpoint for user login to receive JWT access and refresh tokens
    # POST /api/login/
    # This endpoint allows a user to log in using either their email or phone number and password.
    # Upon successful authentication, the API will return JWT access and refresh tokens.
    #
    # Example Request Body:
    # {
    #     "email_or_phone": "john.doe@example.com",
    #     "password": "password123"
    # }
    #
    # Example Response:
    # {
    #     "access": "jwt_access_token",
    #     "refresh": "jwt_refresh_token"
    # }
    path('login/', LoginView.as_view(), name='login'),

    # Endpoint to get the list of specializations (equipment types)
    # GET /api/specializations/
    # This endpoint provides a list of all specializations (e.g., elevators, generators, HVAC systems).
    # It is not protected and can be used to populate a dropdown in the frontend.
    #
    # Example Response:
    # [
    #     {"id": 1, "name": "Elevators"},
    #     {"id": 2, "name": "Power Backup Generators"},
    #     {"id": 3, "name": "HVAC Systems"}
    # ]
    path('specializations/', SpecializationListView.as_view(), name='specializations'),

        # This endpoint returns a list of maintenance companies based on specialization.
    # The endpoint is designed to allow clients to query maintenance companies that specialize in a given field.
    #
    # URL: /api/maintenance-companies/
    # Method: GET
    #
    # Query Parameters:
    #   - specialization (string): This is a required query parameter. It specifies the type of service the maintenance companies specialize in (e.g., "Elevators", "Plumbing").
    #
    # Responses:
    #   - On success (status code 200):
    #     Returns a JSON array of maintenance companies that match the specialization.
    #     Each company will have:
    #       - "company_name" (string): The name of the maintenance company.
    #       - "id" (integer): The primary key (ID) of the maintenance company.
    #     Example response:
    #       [
    #         {
    #           "company_name": "Elevator Experts",
    #           "id": 1
    #         },
    #         {
    #           "company_name": "Lift Services",
    #           "id": 2
    #         }
    #       ]
    #
    #   - On failure (status code 400 or 404):
    #     If no specialization parameter is provided, or if no maintenance companies are found for the given specialization, 
    #     an error message will be returned with an appropriate HTTP status code.
    #     Example error responses:
    #       - If no specialization parameter is provided (status 400):
    #         {
    #           "error": "Specialization is required"
    #         }
    #       - If no companies are found for the given specialization (status 404):
    #         {
    #           "error": "No companies found dealing with Elevators"
    #         }
    #
    # This view allows any user (authenticated or not) to access the data.
    #path('maintenance-companies/', MaintenanceListView.as_view(), name='maintenance-companies-list'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # {
    # "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTczNDA3NzI5OCwiaWF0IjoxNzMzOTkwODk4LCJqdGkiOiI2ZTJhODExNzdlM2U0YWUxODYwY2M5MjcxMTMwMTBlZCIsInVzZXJfaWQiOjF9.dbryfrKrHG3u5Ox-CSp7l5qFczAlROPeLMyQhPa3Rr4",
    # "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzMzOTkxMTk4LCJpYXQiOjE3MzM5OTA4OTgsImp0aSI6IjViYTAwOTAyZTlhMDQzYmU4YzY3NDRiYzRlM2EwZmNjIiwidXNlcl9pZCI6MX0.iEoD96y2Xg-PSu6kdLHn32SjPvdP5Am7gmdPggWr_lg"
    # }
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('maintenance-companies/', include('maintenance_companies.urls', namespace='maintenance_companies')),
    path('technicians/', include('technicians.urls')),
    path('developers/', include('developers.urls')),
    path('buildings/', include('buildings.urls')),
    path('elevators/', include('elevators.urls')),
    path('jobs/', include('jobs.urls')),
    path('signup/', csrf_exempt(SignUpView.as_view()), name='signup-api'),
    path('alerts/', include('alerts.urls')),
    path('brokers/', include('brokers.urls')),
    path('payments/', include('payments.urls')),


]
