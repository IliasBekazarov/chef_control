from django.contrib.auth.models import User
from rest_framework import serializers
from .models import UserProfile, DetectionSession, DetectionRecord, AlertSettings


# ─── Auth ───────────────────────────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = UserProfile
        fields = ["role", "avatar", "location"]


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = ["id", "username", "email", "first_name", "last_name", "full_name",
                  "is_staff", "date_joined", "profile"]

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)
    role      = serializers.ChoiceField(choices=["admin", "user"], default="user", write_only=True)

    class Meta:
        model  = User
        fields = ["username", "email", "first_name", "last_name", "password", "password2", "role"]

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Сырсөздөр дал келбейт"})
        return data

    def create(self, validated_data):
        role = validated_data.pop("role", "user")
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user, role=role)
        return user


# ─── Detection ──────────────────────────────────────────────────────────────
class DetectionRecordSerializer(serializers.ModelSerializer):
    violations_list = serializers.SerializerMethodField()

    class Meta:
        model  = DetectionRecord
        fields = [
            "id", "session", "timestamp", "person_count",
            "has_hat", "hat_confidence",
            "has_apron", "apron_confidence",
            "is_compliant", "violations", "violations_list",
            "frame_image", "created_at",
        ]

    def get_violations_list(self, obj):
        return obj.violations_list()


class DetectionSessionSerializer(serializers.ModelSerializer):
    compliance_rate = serializers.ReadOnlyField()
    records_count   = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model  = DetectionSession
        fields = [
            "id", "session_id", "started_at", "ended_at",
            "total_checks", "violations", "compliance_rate",
            "records_count", "notes", "created_by_name",
        ]

    def get_records_count(self, obj):
        return obj.records.count()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return "System"


# ─── Alert Settings ─────────────────────────────────────────────────────────
class AlertSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model  = AlertSettings
        fields = [
            "enabled", "bot_token", "chat_id",
            "violation_threshold", "cooldown_minutes",
            "last_alert_at", "consecutive_violations",
        ]
        read_only_fields = ["last_alert_at", "consecutive_violations"]


# ─── Dashboard stats ────────────────────────────────────────────────────────
class DashboardStatsSerializer(serializers.Serializer):
    total_checks      = serializers.IntegerField()
    total_violations  = serializers.IntegerField()
    compliance_rate   = serializers.FloatField()
    total_sessions    = serializers.IntegerField()
    active_users      = serializers.IntegerField()
    today_checks      = serializers.IntegerField()
    today_violations  = serializers.IntegerField()
    weekly_trend      = serializers.ListField()
    top_violations    = serializers.ListField()
