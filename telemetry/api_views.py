from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .influx_repo import get_influx_repo
from .models import CsvImport, MeasuredQuantity, MotorGroup, Sensor, SensorChannel, Session
from .serializers import (
    MeasuredQuantitySerializer,
    MotorGroupSerializer,
    SensorChannelSerializer,
    SensorSerializer,
    SessionSerializer,
)
from .services import import_csv_to_session


class MotorGroupViewSet(viewsets.ModelViewSet):
    queryset = MotorGroup.objects.all()
    serializer_class = MotorGroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.select_related("motor_group").all()
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]


class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.select_related("stand").all()
    serializer_class = SensorSerializer
    permission_classes = [permissions.IsAuthenticated]


class SensorChannelViewSet(viewsets.ModelViewSet):
    queryset = SensorChannel.objects.select_related("sensor", "quantity").all()
    serializer_class = SensorChannelSerializer
    permission_classes = [permissions.IsAuthenticated]


class MeasuredQuantityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MeasuredQuantity.objects.all()
    serializer_class = MeasuredQuantitySerializer
    permission_classes = [permissions.IsAuthenticated]


class SessionSeriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _parse_dt(self, raw):
        if not raw:
            return None
        dt = parse_datetime(raw)
        if dt and timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt

    def get(self, request, pk: int):
        quantity_key = request.query_params.get("quantity")
        if not quantity_key:
            return Response({"detail": "quantity is required"}, status=400)

        session = get_object_or_404(Session, pk=pk)
        try:
            quantity = MeasuredQuantity.objects.get(key=quantity_key)
        except MeasuredQuantity.DoesNotExist:
            return Response({"detail": "unknown quantity"}, status=404)

        from_dt = self._parse_dt(request.query_params.get("from"))
        to_dt = self._parse_dt(request.query_params.get("to"))

        repo = get_influx_repo()
        data = repo.query_series(session_id=session.id, quantity=quantity.key, from_dt=from_dt, to_dt=to_dt)
        return Response(data)


class SessionImportCsvView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, pk: int):
        session = get_object_or_404(Session, pk=pk)
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "file is required"}, status=400)
        csv_import = import_csv_to_session(session, upload, file_name=upload.name)
        status_code = 200 if csv_import.status == CsvImport.STATUS_SUCCESS else 400
        return Response(
            {
                "status": csv_import.status,
                "rows_processed": csv_import.rows_processed,
                "rows_failed": csv_import.rows_failed,
                "error_message": csv_import.error_message,
            },
            status=status_code,
        )
