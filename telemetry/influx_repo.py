from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from django.conf import settings
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


class InfluxRepository:
    def __init__(self, url: str, token: str, org: str, bucket: str, measurement: str = "readings") -> None:
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self.measurement = measurement

    def _client(self) -> InfluxDBClient:
        return InfluxDBClient(url=self.url, token=self.token, org=self.org)

    def write_points(self, session, points: Iterable[dict]) -> None:
        """Write list of points to InfluxDB.

        Each point should have keys: ts (datetime or ISO string), value (float), sensor_id, quantity.
        """
        influx_points = []
        for p in points:
            ts = p.get("ts")
            if isinstance(ts, datetime):
                ts_value = ts.isoformat()
            else:
                ts_value = ts
            try:
                value = float(p.get("value"))
            except (TypeError, ValueError):
                continue
            influx_points.append(
                Point(self.measurement)
                .tag("session_id", str(session.id))
                .tag("motor_group_id", str(session.motor_group_id))
                .tag("sensor_id", str(p.get("sensor_id") or ""))
                .tag("quantity", str(p.get("quantity") or ""))
                .field("value", value)
                .time(ts_value)
            )

        if not influx_points:
            return

        with self._client() as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            write_api.write(bucket=self.bucket, org=self.org, record=influx_points)

    def query_series(self, session_id: int, quantity: str, from_dt: Optional[datetime] = None, to_dt: Optional[datetime] = None) -> List[dict]:
        start_expr = f'time(v: "{from_dt.isoformat()}")' if from_dt else "0"
        stop_expr = f'time(v: "{to_dt.isoformat()}")' if to_dt else "now()"
        flux = f"""
from(bucket: \"{self.bucket}\")
  |> range(start: {start_expr}, stop: {stop_expr})
  |> filter(fn: (r) => r._measurement == \"{self.measurement}\")
  |> filter(fn: (r) => r.quantity == \"{quantity}\" and r.session_id == \"{session_id}\")
  |> keep(columns: [\"_time\", \"_value\"])
  |> sort(columns: [\"_time\"])
"""
        with self._client() as client:
            tables = client.query_api().query(flux)
        data = []
        for table in tables:
            for record in table.records:
                data.append({"ts": record.get_time().isoformat(), "value": record.get_value()})
        return data

    def query_last_points(self, session_id: int, quantity: str, limit: int = 200) -> List[dict]:
        flux = f"""
from(bucket: \"{self.bucket}\")
  |> range(start: 0)
  |> filter(fn: (r) => r._measurement == \"{self.measurement}\")
  |> filter(fn: (r) => r.quantity == \"{quantity}\" and r.session_id == \"{session_id}\")
  |> sort(columns: [\"_time\"], desc: true)
  |> limit(n: {limit})
  |> sort(columns: [\"_time\"])
"""
        with self._client() as client:
            tables = client.query_api().query(flux)
        data = []
        for table in tables:
            for record in table.records:
                data.append({"ts": record.get_time().isoformat(), "value": record.get_value()})
        return data


def get_influx_repo() -> InfluxRepository:
    cfg = getattr(settings, "INFLUX_SETTINGS", {})
    return InfluxRepository(
        url=cfg.get("url", "http://localhost:8086"),
        token=cfg.get("token", ""),
        org=cfg.get("org", ""),
        bucket=cfg.get("bucket", ""),
    )
