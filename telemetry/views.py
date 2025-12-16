from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import MotorGroupForm, SensorForm, SessionForm
from .models import CsvImport, MeasuredQuantity, MotorGroup, Sensor, Session, Stand


def redirect_to_sessions(request):
    return redirect("telemetry:session_list")


class MotorGroupListView(LoginRequiredMixin, ListView):
    model = MotorGroup
    template_name = "telemetry/motor_group_list.html"
    context_object_name = "motor_groups"


class MotorGroupCreateView(LoginRequiredMixin, CreateView):
    model = MotorGroup
    form_class = MotorGroupForm
    template_name = "telemetry/motor_group_form.html"
    success_url = reverse_lazy("telemetry:motor_group_list")

    def form_valid(self, form):
        messages.success(self.request, "Группа добавлена")
        return super().form_valid(form)


class MotorGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = MotorGroup
    form_class = MotorGroupForm
    template_name = "telemetry/motor_group_form.html"
    success_url = reverse_lazy("telemetry:motor_group_list")

    def form_valid(self, form):
        messages.success(self.request, "Группа обновлена")
        return super().form_valid(form)


class MotorGroupDeleteView(LoginRequiredMixin, DeleteView):
    model = MotorGroup
    template_name = "telemetry/confirm_delete.html"
    success_url = reverse_lazy("telemetry:motor_group_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Группа удалена")
        return super().delete(request, *args, **kwargs)


class SensorListView(LoginRequiredMixin, ListView):
    model = Sensor
    template_name = "telemetry/sensor_list.html"
    context_object_name = "sensors"

    def get_queryset(self):
        return Sensor.objects.select_related("stand").prefetch_related("channels__quantity").all()


class SensorCreateView(LoginRequiredMixin, CreateView):
    model = Sensor
    form_class = SensorForm
    template_name = "telemetry/sensor_form.html"
    success_url = reverse_lazy("telemetry:sensor_list")

    def get_initial(self):
        initial = super().get_initial()
        stand = Stand.objects.first()
        if stand:
            initial["stand"] = stand
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Датчик добавлен")
        return super().form_valid(form)


class SensorUpdateView(LoginRequiredMixin, UpdateView):
    model = Sensor
    form_class = SensorForm
    template_name = "telemetry/sensor_form.html"
    success_url = reverse_lazy("telemetry:sensor_list")

    def form_valid(self, form):
        messages.success(self.request, "Датчик обновлен")
        return super().form_valid(form)


class SensorDeleteView(LoginRequiredMixin, DeleteView):
    model = Sensor
    template_name = "telemetry/confirm_delete.html"
    success_url = reverse_lazy("telemetry:sensor_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Датчик удален")
        return super().delete(request, *args, **kwargs)


class SessionListView(LoginRequiredMixin, ListView):
    model = Session
    template_name = "telemetry/session_list.html"
    context_object_name = "sessions"

    def get_queryset(self):
        return Session.objects.select_related("motor_group").all()


class SessionCreateView(LoginRequiredMixin, CreateView):
    model = Session
    form_class = SessionForm
    template_name = "telemetry/session_form.html"
    success_url = reverse_lazy("telemetry:session_list")

    def form_valid(self, form):
        messages.success(self.request, "Сессия добавлена")
        return super().form_valid(form)


class SessionUpdateView(LoginRequiredMixin, UpdateView):
    model = Session
    form_class = SessionForm
    template_name = "telemetry/session_form.html"
    success_url = reverse_lazy("telemetry:session_list")

    def form_valid(self, form):
        messages.success(self.request, "Сессия обновлена")
        return super().form_valid(form)


class SessionDeleteView(LoginRequiredMixin, DeleteView):
    model = Session
    template_name = "telemetry/confirm_delete.html"
    success_url = reverse_lazy("telemetry:session_list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Сессия удалена")
        return super().delete(request, *args, **kwargs)


class SessionDetailView(LoginRequiredMixin, DetailView):
    model = Session
    template_name = "telemetry/session_detail.html"
    context_object_name = "session"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["imports"] = self.object.csv_imports.all()
        ctx["quantities"] = MeasuredQuantity.objects.all()
        return ctx
