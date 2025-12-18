from django import forms

from .models import MeasuredQuantity, MotorGroup, Sensor, SensorChannel, Session


class MotorGroupForm(forms.ModelForm):
    class Meta:
        model = MotorGroup
        fields = ["name", "description"]


class SensorForm(forms.ModelForm):
    quantities = forms.ModelMultipleChoiceField(
        queryset=MeasuredQuantity.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Измеряемые величины",
    )

    class Meta:
        model = Sensor
        fields = ["stand", "name", "description", "quantities"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantities"].queryset = MeasuredQuantity.objects.all()
        if self.instance.pk:
            self.fields["quantities"].initial = self.instance.channels.values_list("quantity_id", flat=True)

    def _save_quantities(self, sensor: Sensor):
        selected_ids = set(self.cleaned_data.get("quantities", []).values_list("id", flat=True))
        existing_ids = set(sensor.channels.values_list("quantity_id", flat=True))
        to_add = selected_ids - existing_ids
        to_remove = existing_ids - selected_ids
        for quantity_id in to_add:
            SensorChannel.objects.get_or_create(sensor=sensor, quantity_id=quantity_id)
        if to_remove:
            SensorChannel.objects.filter(sensor=sensor, quantity_id__in=to_remove).delete()

    def save(self, commit=True):
        sensor = super().save(commit)
        if commit:
            self._save_quantities(sensor)
        else:
            original_save_m2m = getattr(self, "save_m2m", None)

            def _save_m2m():
                if original_save_m2m:
                    original_save_m2m()
                self._save_quantities(sensor)

            self.save_m2m = _save_m2m  # type: ignore[assignment]
        return sensor


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["motor_group", "name", "started_at", "ended_at", "notes"]
        widgets = {
            "started_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ended_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ["started_at", "ended_at"]:
            self.fields[field].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]

    def clean(self):
        cleaned = super().clean()
        started_at = cleaned.get("started_at")
        ended_at = cleaned.get("ended_at")
        if started_at and ended_at and ended_at < started_at:
            self.add_error("ended_at", "Дата окончания не может быть раньше начала")
        return cleaned
