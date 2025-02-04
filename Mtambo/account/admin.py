from django.contrib import admin
from .models import User

# Register all models at once
for model in [User]:
    admin.site.register(model)
