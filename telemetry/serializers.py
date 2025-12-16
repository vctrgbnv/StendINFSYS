from rest_framework import serializers

from .models import MeasuredQuantity, MotorGroup, Sensor, SensorChannel, Session


class MotorGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotorGroup
        fields = ["id", "name", "description", "created_at"]


class SessionSerializer(serializers.ModelSerializer):
    motor_group_name = serializers.CharField(source="motor_group.name", read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "motor_group",
            "motor_group_name",
            "name",
            "started_at",
            "ended_at",
            "notes",
            "created_at",
        ]


class SensorSerializer(serializers.ModelSerializer):
    stand_name = serializers.CharField(source="stand.name", read_only=True)

    class Meta:
        model = Sensor
        fields = ["id", "stand", "stand_name", "name", "description", "created_at"]


class SensorChannelSerializer(serializers.ModelSerializer):
    sensor_name = serializers.CharField(source="sensor.name", read_only=True)
    quantity_key = serializers.CharField(source="quantity.key", read_only=True)
    quantity_name = serializers.CharField(source="quantity.name", read_only=True)

    class Meta:
        model = SensorChannel
        fields = ["id", "sensor", "sensor_name", "quantity", "quantity_key", "quantity_name", "label"]


class MeasuredQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasuredQuantity
        fields = ["id", "key", "name", "unit"]
