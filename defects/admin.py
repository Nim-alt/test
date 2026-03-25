from django.contrib import admin
from .models import Defect

@admin.register(Defect)
class DefectAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'status', 'severity', 'priority', 'assigned_to', 'date_reported']
    list_filter = ['status', 'severity', 'priority']
    search_fields = ['title', 'description', 'reporter_email']