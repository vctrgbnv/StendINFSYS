from __future__ import annotations

import csv
import io

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .influx_repo import get_influx_repo
from .models import CsvImport, MeasuredQuantity, Sensor, SensorChannel, Session, Stand


REQUIRED_COLUMNS = ["ts", "throttle", "temperature", "humidity", "rpm", "noise", "thrust"]
QUANTITY_FIELDS = {
    "throttle": "throttle",
    "temperature": "temperature",
    "humidity": "humidity",
    "rpm": "rpm",
    "noise": "noise",
    "thrust": "thrust",
}


def ensure_default_stand() -> Stand:
    stand = Stand.objects.first()
    if stand:
        return stand
    return Stand.objects.create(name="Default Stand")


def resolve_sensor_for_quantity(quantity: MeasuredQuantity, sensor_cache: dict) -> Sensor:
    if quantity.key in sensor_cache:
        return sensor_cache[quantity.key]
    channel = (
        SensorChannel.objects.select_related("sensor")
        .filter(quantity=quantity)
        .order_by("sensor_id")
        .first()
    )
    if channel:
        sensor_cache[quantity.key] = channel.sensor
        return channel.sensor
    stand = ensure_default_stand()
    sensor, _ = Sensor.objects.get_or_create(stand=stand, name="Auto Sensor")
    SensorChannel.objects.get_or_create(sensor=sensor, quantity=quantity)
    sensor_cache[quantity.key] = sensor
    return sensor


def parse_timestamp(raw: str):
    if not raw:
        return None
    raw = raw.strip()
    dt = parse_datetime(raw)
    if dt and timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


def import_csv_to_session(session: Session, file_obj, file_name: str | None = None) -> CsvImport:
    csv_import = CsvImport.objects.create(
        session=session,
        status=CsvImport.STATUS_PENDING,
        file_name=file_name or getattr(file_obj, "name", ""),
    )
    sensor_cache = {}
    processed = 0
    failed = 0
    points: list[dict] = []

    try:
        content = file_obj.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            raise ValueError("Пустой CSV")
        normalized_headers = [h.strip().lower() for h in reader.fieldnames]
        missing = {col for col in REQUIRED_COLUMNS if col not in normalized_headers}
        if missing:
            raise ValueError(f"Отсутствуют колонки: {', '.join(sorted(missing))}")

        quantity_map = {key: MeasuredQuantity.objects.get(key=val) for key, val in QUANTITY_FIELDS.items()}
        repo = get_influx_repo()

        for row in reader:
            normalized = {k.strip().lower(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            ts = parse_timestamp(normalized.get("ts", ""))
            if not ts:
                failed += 1
                continue
            row_points = []
            row_failed = False
            for column, quantity_key in QUANTITY_FIELDS.items():
                raw_val = normalized.get(column)
                if raw_val in (None, ""):
                    continue
                try:
                    value = float(raw_val)
                except (TypeError, ValueError):
                    row_failed = True
                    break
                sensor = resolve_sensor_for_quantity(quantity_map[quantity_key], sensor_cache)
                row_points.append(
                    {
                        "ts": ts,
                        "value": value,
                        "sensor_id": sensor.id,
                        "quantity": quantity_key,
                    }
                )
            if row_failed:
                failed += 1
                continue
            if row_points:
                points.extend(row_points)
                processed += 1
            else:
                failed += 1

        if points:
            repo.write_points(session, points)

        csv_import.status = CsvImport.STATUS_SUCCESS
    except Exception as exc:  # noqa: BLE001
        csv_import.status = CsvImport.STATUS_FAILED
        csv_import.error_message = str(exc)
    finally:
        csv_import.rows_processed = processed
        csv_import.rows_failed = failed
        csv_import.finished_at = timezone.now()
        csv_import.save()
    return csv_import
