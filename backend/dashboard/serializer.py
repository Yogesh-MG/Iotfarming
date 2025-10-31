# serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Device, SensorReading, PumpCommand, CurrentStatus


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model. Used for /api/me/ and admin user creation.
    """
    full_name = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, validators=[validate_password], required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'password',
            'full_name', 'date_joined', 'is_active', 'is_staff'  # Added is_staff for role hint
        ]
        read_only_fields = ['id', 'date_joined', 'is_active']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def create(self, validated_data):
        # Password handling for admin creation
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class DeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for Device model. Supports creation by admin (one per user).
    """
    class Meta:
        model = Device
        fields = ['id', 'user', 'name', 'device_id', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SensorReadingSerializer(serializers.ModelSerializer):
    """
    Serializer for SensorReading. Used for history in status.
    """
    class Meta:
        model = SensorReading
        fields = ['id', 'moisture_level', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class PumpCommandSerializer(serializers.ModelSerializer):
    """
    Serializer for PumpCommand. For action history.
    """
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = PumpCommand
        fields = ['id', 'action', 'action_display', 'triggered_by', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class CurrentStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for CurrentStatus snapshot.
    """
    class Meta:
        model = CurrentStatus
        fields = ['current_moisture', 'pump_status', 'last_updated','auto_mode']
        read_only_fields = ['last_updated']


class StatusResponseSerializer(serializers.Serializer):
    """
    Combined serializer for /api/status/ response.
    """
    soil_moisture = serializers.FloatField()
    motor_status = serializers.BooleanField(source='pump_status')
    timestamp = serializers.DateTimeField()
    history = SensorReadingSerializer(many=True)
    actions = PumpCommandSerializer(many=True, source='commands')  # Last 10


class ReadingInputSerializer(serializers.Serializer):
    """
    For ESP POST /api/readings/ - minimal validation.
    """
    # device_id = serializers.CharField(max_length=50)  # Removed: Redundant with API key auth
    moisture = serializers.FloatField(min_value=0, max_value=100)
    ack_command_ids = serializers.ListField(
        child=serializers.IntegerField(), 
        required=False, 
        help_text='IDs of commands to acknowledge after execution'
    )

class PumpUpdateSerializer(serializers.Serializer):
    """
    For /api/update/ POST - pump toggle.
    """
    pump_state = serializers.BooleanField()
    
class AutoModeSerializer(serializers.Serializer):
    """
     For /api/auto-mode/ POST - enable/disable auto mode.
    """
    enabled = serializers.BooleanField()

