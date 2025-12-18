import io
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from rest_framework.test import APIClient

from .forms import SessionForm
from .models import CsvImport, MeasuredQuantity, MotorGroup, Session
from .services import QUANTITY_FIELDS, import_csv_to_session


class SessionFormTests(TestCase):
    def setUp(self):
        self.motor_group = MotorGroup.objects.create(name="Group 1")

    def test_ended_at_cannot_be_before_started_at(self):
        started_at = datetime.utcnow()
        ended_at = started_at - timedelta(hours=1)
        form = SessionForm(
            data={
                "motor_group": self.motor_group.id,
                "name": "Test Session",
                "started_at": started_at.strftime("%Y-%m-%dT%H:%M"),
                "ended_at": ended_at.strftime("%Y-%m-%dT%H:%M"),
                "notes": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("ended_at", form.errors)


class ImportCsvServiceTests(TestCase):
    def setUp(self):
        self.motor_group = MotorGroup.objects.create(name="Group 1")
        for key in QUANTITY_FIELDS.values():
            MeasuredQuantity.objects.get_or_create(key=key, defaults={"name": key, "unit": "u"})

    def test_import_marks_failed_when_no_valid_rows(self):
        session = Session.objects.create(motor_group=self.motor_group, name="Test Session")
        bad_csv = "ts,throttle,temperature,humidity,rpm,noise,thrust\nnot-a-date,foo,bar,baz,qux,quux,corge\n"
        with patch("telemetry.services.get_influx_repo") as mock_repo:
            mock_repo.return_value = type("Repo", (), {"write_points": lambda *args, **kwargs: None})()
            csv_import = import_csv_to_session(session, io.StringIO(bad_csv))
        self.assertEqual(csv_import.status, CsvImport.STATUS_FAILED)
        self.assertEqual(csv_import.rows_processed, 0)
        self.assertGreaterEqual(csv_import.rows_failed, 1)
        self.assertTrue(csv_import.error_message)


class SessionSeriesApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="user", password="pass")
        self.client.login(username="user", password="pass")
        motor_group = MotorGroup.objects.create(name="Group 1")
        self.session = Session.objects.create(motor_group=motor_group, name="Session 1")
        MeasuredQuantity.objects.get_or_create(key="temperature", defaults={"name": "Temp", "unit": "C"})

    def test_invalid_datetime_returns_400(self):
        resp = self.client.get(f"/api/sessions/{self.session.id}/series/?quantity=temperature&from=bad-date")
        self.assertEqual(resp.status_code, 400)
