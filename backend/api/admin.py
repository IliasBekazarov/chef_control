from django.contrib import admin
from .models import UserProfile, DetectionSession, DetectionRecord


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "role", "location"]
    list_filter  = ["role"]


@admin.register(DetectionSession)
class DetectionSessionAdmin(admin.ModelAdmin):
    list_display  = ["session_id", "started_at", "total_checks", "violations", "compliance_rate"]
    list_filter   = ["started_at"]
    search_fields = ["session_id", "notes"]


@admin.register(DetectionRecord)
class DetectionRecordAdmin(admin.ModelAdmin):
    list_display  = ["timestamp", "is_compliant", "has_hat", "has_apron", "violations"]
    list_filter   = ["is_compliant", "has_hat", "has_apron"]
    search_fields = ["violations"]
