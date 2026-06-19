from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register("sessions", views.DetectionSessionViewSet, basename="session")
router.register("records",  views.DetectionRecordViewSet,  basename="record")

urlpatterns = [
    # Auth
    path("auth/login/",   views.CustomTokenView.as_view(),  name="token_obtain"),
    path("auth/refresh/", TokenRefreshView.as_view(),        name="token_refresh"),
    path("auth/register/",views.RegisterView.as_view(),      name="register"),
    path("auth/me/",      views.MeView.as_view(),            name="me"),
    # Users
    path("users/",        views.UserListView.as_view(),      name="users"),
    # Dashboard
    path("dashboard/",    views.DashboardStatsView.as_view(),name="dashboard"),
    # Ingest
    path("ingest/",       views.ingest_record,               name="ingest"),
    # Alert Settings
    path("settings/alerts/",      views.AlertSettingsView.as_view(), name="alert-settings"),
    path("settings/alerts/test/", views.test_alert,                  name="alert-test"),
    # PDF Reports
    path("reports/pdf/session/<str:session_id>/", views.pdf_session_report, name="pdf-session"),
    path("reports/pdf/range/",                    views.pdf_range_report,   name="pdf-range"),
    # Camera
    path("camera/", views.CameraControlView.as_view(), name="camera-control"),
    # Training
    path("training/status/", views.training_status, name="training-status"),
    path("training/start/",  views.training_start,  name="training-start"),
    path("training/stop/",   views.training_stop,   name="training-stop"),
    # ViewSets
    path("", include(router.urls)),
]
