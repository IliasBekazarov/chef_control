from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import UserProfile, DetectionSession, DetectionRecord
from .serializers import (
    UserSerializer, RegisterSerializer,
    DetectionSessionSerializer, DetectionRecordSerializer,
    DashboardStatsSerializer,
)


# ─── Custom JWT ─────────────────────────────────────────────────────────────
class CustomTokenSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class CustomTokenView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer


# ─── Auth ───────────────────────────────────────────────────────────────────
class RegisterView(generics.CreateAPIView):
    queryset         = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        # Update profile fields
        profile_data = request.data.pop("profile", {})
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if profile_data and hasattr(user, "profile"):
            for key, val in profile_data.items():
                setattr(user.profile, key, val)
            user.profile.save()
        return Response(UserSerializer(user).data)


# ─── Users (Admin only) ─────────────────────────────────────────────────────
class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated and
                (request.user.is_staff or
                 getattr(getattr(request.user, "profile", None), "role", "") == "admin"))


class UserListView(generics.ListAPIView):
    queryset         = User.objects.select_related("profile").all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    filter_backends  = [SearchFilter, OrderingFilter]
    search_fields    = ["username", "email", "first_name", "last_name"]
    ordering_fields  = ["date_joined", "username"]


# ─── Detection Sessions ─────────────────────────────────────────────────────
class DetectionSessionViewSet(viewsets.ModelViewSet):
    queryset         = DetectionSession.objects.all()
    serializer_class = DetectionSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["session_id"]
    search_fields    = ["session_id", "notes"]
    ordering_fields  = ["started_at", "total_checks", "violations"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        is_admin = (user.is_staff or
                    getattr(getattr(user, "profile", None), "role", "") == "admin")
        if not is_admin:
            qs = qs.filter(created_by=user)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# ─── Detection Records ──────────────────────────────────────────────────────
class DetectionRecordViewSet(viewsets.ModelViewSet):
    queryset         = DetectionRecord.objects.select_related("session").all()
    serializer_class = DetectionRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["is_compliant", "has_hat", "has_apron", "session"]
    ordering_fields  = ["timestamp", "created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        is_admin = (user.is_staff or
                    getattr(getattr(user, "profile", None), "role", "") == "admin")
        if not is_admin:
            qs = qs.filter(session__created_by=user)
        return qs


# ─── Dashboard Stats ────────────────────────────────────────────────────────
class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user     = request.user
        is_admin = (user.is_staff or
                    getattr(getattr(user, "profile", None), "role", "") == "admin")

        records_qs  = DetectionRecord.objects.all()
        sessions_qs = DetectionSession.objects.all()
        if not is_admin:
            records_qs  = records_qs.filter(session__created_by=user)
            sessions_qs = sessions_qs.filter(created_by=user)

        today = timezone.now().date()
        total_checks     = records_qs.count()
        total_violations = records_qs.filter(is_compliant=False).count()
        compliance_rate  = (
            round((total_checks - total_violations) / total_checks * 100, 1)
            if total_checks else 0.0
        )

        today_qs         = records_qs.filter(timestamp__date=today)
        today_checks     = today_qs.count()
        today_violations = today_qs.filter(is_compliant=False).count()

        # 7 күндүк тренд
        weekly_trend = []
        for i in range(6, -1, -1):
            day      = today - timedelta(days=i)
            day_qs   = records_qs.filter(timestamp__date=day)
            chks     = day_qs.count()
            viols    = day_qs.filter(is_compliant=False).count()
            weekly_trend.append({
                "date":       day.strftime("%m/%d"),
                "checks":     chks,
                "violations": viols,
                "compliant":  chks - viols,
            })

        # Эң кеп учураган бузуулар
        top_violations = []
        all_viols = records_qs.filter(is_compliant=False).values_list("violations", flat=True)
        viol_counter = {}
        for v_str in all_viols:
            for part in v_str.split("|"):
                part = part.strip()
                if part:
                    viol_counter[part] = viol_counter.get(part, 0) + 1
        for name, cnt in sorted(viol_counter.items(), key=lambda x: -x[1])[:5]:
            top_violations.append({"name": name, "count": cnt})

        data = {
            "total_checks":     total_checks,
            "total_violations": total_violations,
            "compliance_rate":  compliance_rate,
            "total_sessions":   sessions_qs.count(),
            "active_users":     User.objects.filter(is_active=True).count() if is_admin else 1,
            "today_checks":     today_checks,
            "today_violations": today_violations,
            "weekly_trend":     weekly_trend,
            "top_violations":   top_violations,
        }
        return Response(data)


# ─── Ingest (CV модели жазат) ───────────────────────────────────────────────
@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def ingest_record(request):
    """
    CV pipeline жактан маалымат жазуу endpoint.
    POST /api/ingest/
    """
    data = request.data
    session_id = data.get("session_id")
    session, _ = DetectionSession.objects.get_or_create(
        session_id=session_id,
        defaults={"created_by": request.user},
    )

    record = DetectionRecord.objects.create(
        session          = session,
        timestamp        = data.get("timestamp"),
        person_count     = data.get("person_count", 0),
        has_hat          = data.get("has_hat", False),
        hat_confidence   = data.get("hat_confidence", 0.0),
        has_apron        = data.get("has_apron", False),
        apron_confidence = data.get("apron_confidence", 0.0),
        is_compliant     = data.get("is_compliant", False),
        violations       = data.get("violations", ""),
    )

    # Session статистикасын жаңылоо
    session.total_checks += 1
    if not record.is_compliant:
        session.violations += 1
    session.save()

    return Response(DetectionRecordSerializer(record).data, status=status.HTTP_201_CREATED)
