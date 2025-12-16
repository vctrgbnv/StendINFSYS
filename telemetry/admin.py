from django.contrib import admin

from .models import CsvImport, MeasuredQuantity, MotorGroup, Sensor, SensorChannel, Session, Stand


@admin.register(Stand)
class StandAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "created_at")
    search_fields = ("name", "location")


@admin.register(MotorGroup)
class MotorGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("name", "motor_group", "started_at", "ended_at")
    list_filter = ("motor_group",)
    search_fields = ("name", "notes")


@admin.register(MeasuredQuantity)
class MeasuredQuantityAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "unit")
    search_fields = ("key", "name")


class SensorChannelInline(admin.TabularInline):
    model = SensorChannel
    extra = 0


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ("name", "stand", "created_at")
    search_fields = ("name", "description")
    list_filter = ("stand",)
    inlines = [SensorChannelInline]


@admin.register(CsvImport)
class CsvImportAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "status", "rows_processed", "rows_failed", "created_at", "finished_at")
    list_filter = ("status", "created_at")
    search_fields = ("session__name",)
