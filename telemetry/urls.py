from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .api_views import (
    MeasuredQuantityViewSet,
    MotorGroupViewSet,
    SensorChannelViewSet,
    SensorViewSet,
    SessionSeriesView,
    SessionViewSet,
)

router = DefaultRouter()
router.register(r"motor-groups", MotorGroupViewSet)
router.register(r"sessions", SessionViewSet)
router.register(r"sensors", SensorViewSet)
router.register(r"sensor-channels", SensorChannelViewSet)
router.register(r"quantities", MeasuredQuantityViewSet)

app_name = "telemetry"

urlpatterns = [
    path("", views.redirect_to_sessions, name="home"),
    path("motor-groups/", views.MotorGroupListView.as_view(), name="motor_group_list"),
    path("motor-groups/add/", views.MotorGroupCreateView.as_view(), name="motor_group_add"),
    path("motor-groups/<int:pk>/edit/", views.MotorGroupUpdateView.as_view(), name="motor_group_edit"),
    path("motor-groups/<int:pk>/delete/", views.MotorGroupDeleteView.as_view(), name="motor_group_delete"),

    path("sensors/", views.SensorListView.as_view(), name="sensor_list"),
    path("sensors/add/", views.SensorCreateView.as_view(), name="sensor_add"),
    path("sensors/<int:pk>/edit/", views.SensorUpdateView.as_view(), name="sensor_edit"),
    path("sensors/<int:pk>/delete/", views.SensorDeleteView.as_view(), name="sensor_delete"),

    path("sessions/", views.SessionListView.as_view(), name="session_list"),
    path("sessions/add/", views.SessionCreateView.as_view(), name="session_add"),
    path("sessions/<int:pk>/", views.SessionDetailView.as_view(), name="session_detail"),
    path("sessions/<int:pk>/edit/", views.SessionUpdateView.as_view(), name="session_edit"),
    path("sessions/<int:pk>/delete/", views.SessionDeleteView.as_view(), name="session_delete"),

    path("api/sessions/<int:pk>/series/", SessionSeriesView.as_view(), name="session_series_api"),
    path("api/", include(router.urls)),
]
