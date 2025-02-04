from django.contrib import admin
from django.apps import apps

# Get all models in the app dynamically
app = apps.get_app_config('buildings')  # Replace 'your_app_name' with the actual app name

# Register all models in the app
for model in app.get_models():
    admin.site.register(model)
