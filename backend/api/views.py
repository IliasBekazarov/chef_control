from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone
from django.http import HttpResponse
from datetime import timedelta, date as date_type
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import subprocess, json, csv, signal, os
from pathlib import Path

from rest_framework import viewsets, generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import UserProfile, DetectionSession, DetectionRecord, AlertSettings
from .serializers import (
    UserSerializer, RegisterSerializer,
    DetectionSessionSerializer, DetectionRecordSerializer,
    DashboardStatsSerializer, AlertSettingsSerializer,
)
from .telegram_service import send_alert, send_test_message
from .report_generator import build_session_report, build_range_report


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

    # Telegram алерт (бузуу болсо)
    if not record.is_compliant:
        send_alert(record)

    # WebSocket push — бардык MonitorPage клиенттерине жиберет
    _ws_push(DetectionRecordSerializer(record).data)

    return Response(DetectionRecordSerializer(record).data, status=status.HTTP_201_CREATED)


def _ws_push(record_data: dict):
    try:
        layer = get_channel_layer()
        async_to_sync(layer.group_send)(
            "monitor_updates",
            {"type": "detection_update", "data": record_data},
        )
    except Exception:
        pass  # WebSocket жок болсо HTTP жооп бузулбасын


# ─── Alert Settings ──────────────────────────────────────────────────────────
class AlertSettingsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        cfg = AlertSettings.get()
        return Response(AlertSettingsSerializer(cfg).data)

    def put(self, request):
        cfg = AlertSettings.get()
        ser = AlertSettingsSerializer(cfg, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data)


@api_view(["POST"])
@permission_classes([IsAdminRole])
def test_alert(request):
    """Тест Telegram билдируу жиберет"""
    data = request.data
    token = data.get("bot_token", "").strip()
    chat  = data.get("chat_id", "").strip()

    if not token or not chat:
        return Response({"error": "bot_token жана chat_id талап кылынат"},
                        status=status.HTTP_400_BAD_REQUEST)

    ok, err = send_test_message(token, chat)
    if ok:
        return Response({"success": True, "message": "Тест алерт жиберилди ✅"})
    return Response({"success": False, "error": err or "Telegram API ката кайтарды"},
                    status=status.HTTP_400_BAD_REQUEST)


# ─── PDF Reports ─────────────────────────────────────────────────────────────
@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def pdf_session_report(request, session_id):
    """Бир сессия боюнча PDF. GET /api/reports/pdf/session/<session_id>/"""
    user     = request.user
    is_admin = (user.is_staff or
                getattr(getattr(user, "profile", None), "role", "") == "admin")
    try:
        qs = DetectionSession.objects.all()
        if not is_admin:
            qs = qs.filter(created_by=user)
        session = qs.get(session_id=session_id)
    except DetectionSession.DoesNotExist:
        return Response({"error": "Сессия табылган жок"}, status=status.HTTP_404_NOT_FOUND)

    records = list(DetectionRecord.objects.filter(session=session).order_by("timestamp"))
    pdf_bytes = build_session_report(session, records)

    filename = f"chef_report_{session_id}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def pdf_range_report(request):
    """
    Дата диапазону боюнча жалпы PDF.
    GET /api/reports/pdf/range/?date_from=2026-01-01&date_to=2026-06-05
    """
    user     = request.user
    is_admin = (user.is_staff or
                getattr(getattr(user, "profile", None), "role", "") == "admin")

    # Параметрлер
    def _parse_date(s):
        if not s: return None
        try:
            from datetime import datetime
            return datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None

    date_from = _parse_date(request.GET.get("date_from"))
    date_to   = _parse_date(request.GET.get("date_to")) or date_type.today()

    records_qs  = DetectionRecord.objects.all()
    sessions_qs = DetectionSession.objects.all()
    if not is_admin:
        records_qs  = records_qs.filter(session__created_by=user)
        sessions_qs = sessions_qs.filter(created_by=user)

    if date_from:
        records_qs  = records_qs.filter(timestamp__date__gte=date_from)
        sessions_qs = sessions_qs.filter(started_at__date__gte=date_from)
    records_qs  = records_qs.filter(timestamp__date__lte=date_to)
    sessions_qs = sessions_qs.filter(started_at__date__lte=date_to)

    # Weekly trend (акыркы 7 күн же диапазон)
    today = date_type.today()
    weekly_trend = []
    for i in range(6, -1, -1):
        day    = today - timedelta(days=i)
        day_qs = records_qs.filter(timestamp__date=day)
        chks   = day_qs.count()
        viols  = day_qs.filter(is_compliant=False).count()
        weekly_trend.append({
            "date": day.strftime("%d.%m"),
            "checks": chks, "violations": viols, "compliant": chks - viols,
        })

    # Top violations
    viol_counter = {}
    for v_str in records_qs.filter(is_compliant=False).values_list("violations", flat=True):
        for part in v_str.split("|"):
            part = part.strip()
            if part:
                viol_counter[part] = viol_counter.get(part, 0) + 1
    top_violations = [
        {"name": n, "count": c}
        for n, c in sorted(viol_counter.items(), key=lambda x: -x[1])[:5]
    ]

    pdf_bytes = build_range_report(
        records_qs, sessions_qs, date_from, date_to, weekly_trend, top_violations
    )

    d_from = date_from.strftime("%Y%m%d") if date_from else "all"
    d_to   = date_to.strftime("%Y%m%d")
    filename = f"chef_report_{d_from}_{d_to}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


# ─── Training ─────────────────────────────────────────────────────────────────
PROJECT_ROOT    = Path(__file__).resolve().parent.parent.parent
STATUS_FILE     = PROJECT_ROOT / "runs" / "training_status.json"
TRAIN_PID_FILE  = PROJECT_ROOT / "runs" / "training.pid"


def _read_training_status() -> dict:
    """results.csv + status.json'дон учурдагы тренинг абалын окуйт."""
    base = {
        "state": "idle",
        "epoch": 0, "epochs_total": 100,
        "map50": 0.0, "map50_best": 0.0,
        "history": [],
        "error": None,
        "started_at": None, "finished_at": None,
    }

    if STATUS_FILE.exists():
        try:
            saved = json.loads(STATUS_FILE.read_text())
            base.update(saved)
        except Exception:
            pass

    # results.csv дан live маалымат алуу
    run_dir = PROJECT_ROOT / "runs" / "detect" / "chef_detector_v2"
    csv_path = run_dir / "results.csv"
    if csv_path.exists():
        try:
            rows = list(csv.DictReader(open(csv_path)))
            if rows:
                history = []
                for r in rows:
                    ep   = int(float(r.get("                  epoch", r.get("epoch", 0))))
                    m50  = float(r.get("metrics/mAP50(B)", 0))
                    loss = float(r.get("train/box_loss", 0))
                    history.append({"epoch": ep + 1, "map50": round(m50, 4), "loss": round(loss, 4)})
                base["history"] = history
                last = rows[-1]
                base["epoch"]     = int(float(last.get("                  epoch", last.get("epoch", 0)))) + 1
                base["map50"]     = round(float(last.get("metrics/mAP50(B)", 0)), 4)
                base["map50_best"] = round(max(float(r.get("metrics/mAP50(B)", 0)) for r in rows), 4)
        except Exception:
            pass

    # PID файлы бар болсо — тренинг жүрүп жатат
    if TRAIN_PID_FILE.exists():
        try:
            pid = int(TRAIN_PID_FILE.read_text().strip())
            # Process иштеп жатабы?
            os.kill(pid, 0)
            base["state"] = "training"
        except (ProcessLookupError, ValueError):
            TRAIN_PID_FILE.unlink(missing_ok=True)
            if base.get("state") == "training":
                base["state"] = "done"

    return base


@api_view(["GET"])
@permission_classes([IsAdminRole])
def training_status(request):
    return Response(_read_training_status())


@api_view(["POST"])
@permission_classes([IsAdminRole])
def training_start(request):
    """Тренингди фондо баштайт."""
    if TRAIN_PID_FILE.exists():
        try:
            pid = int(TRAIN_PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return Response({"error": "Тренинг буга чейин жүрүп жатат"},
                            status=status.HTTP_409_CONFLICT)
        except (ProcessLookupError, ValueError):
            TRAIN_PID_FILE.unlink(missing_ok=True)

    data       = request.data
    model_name = data.get("model", "yolov8s.pt")
    epochs     = int(data.get("epochs", 100))
    device     = data.get("device", "mps")

    # Эски статус файлын тазалоо
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps({
        "state": "training", "epoch": 0, "epochs_total": epochs,
        "map50": 0.0, "map50_best": 0.0, "history": [],
        "started_at": timezone.now().isoformat(), "finished_at": None, "error": None,
    }))

    script = PROJECT_ROOT / "train_model.py"
    venv_python = PROJECT_ROOT / "venv" / "bin" / "python3"
    python_bin  = str(venv_python) if venv_python.exists() else "python3"

    proc = subprocess.Popen(
        [python_bin, str(script),
         "--model", model_name,
         "--epochs", str(epochs),
         "--device", device],
        cwd=str(PROJECT_ROOT),
        stdout=open(PROJECT_ROOT / "logs" / "training.log", "w"),
        stderr=subprocess.STDOUT,
    )
    TRAIN_PID_FILE.write_text(str(proc.pid))
    return Response({"success": True, "pid": proc.pid, "message": "Тренинг башталды 🚀"})


@api_view(["POST"])
@permission_classes([IsAdminRole])
def training_stop(request):
    if not TRAIN_PID_FILE.exists():
        return Response({"error": "Жүрүп жаткан тренинг жок"},
                        status=status.HTTP_404_NOT_FOUND)
    try:
        pid = int(TRAIN_PID_FILE.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        TRAIN_PID_FILE.unlink(missing_ok=True)
        STATUS_FILE.write_text(json.dumps({"state": "stopped"}))
        return Response({"success": True, "message": "Тренинг токтотулду"})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
