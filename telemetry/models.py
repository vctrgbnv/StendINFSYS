from django.db import models
from django.utils import timezone


class Stand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class MotorGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Session(models.Model):
    motor_group = models.ForeignKey(MotorGroup, on_delete=models.CASCADE, related_name="sessions")
    name = models.CharField(max_length=120)
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"{self.motor_group.name} / {self.name}"


class MeasuredQuantity(models.Model):
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.unit})"


class Sensor(models.Model):
    stand = models.ForeignKey(Stand, on_delete=models.CASCADE, related_name="sensors")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("stand", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.stand.name})"


class SensorChannel(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="channels")
    quantity = models.ForeignKey(MeasuredQuantity, on_delete=models.CASCADE, related_name="sensor_channels")
    label = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["sensor", "quantity"]
        unique_together = [("sensor", "quantity")]

    def __str__(self) -> str:
        label = f" - {self.label}" if self.label else ""
        return f"{self.sensor.name}: {self.quantity.name}{label}"


class CsvImport(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="csv_imports")
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rows_processed = models.PositiveIntegerField(default=0)
    rows_failed = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    file_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Import {self.id} for session {self.session_id}"
