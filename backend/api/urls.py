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
    # ViewSets
    path("", include(router.urls)),
]
