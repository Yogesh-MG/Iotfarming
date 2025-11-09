from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
import secrets



class Device(models.Model):
    """
    Represents the IoT device (ESP32 + pump + sensor) associated with a user.
    For simplicity, assume one device per user; extend for multi-device support.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=100, default='Smart Irrigation Device')
    api_key = models.CharField(max_length=64, unique=True, default=secrets.token_hex(32))
    device_id = models.CharField(max_length=50, unique=True, help_text='Unique ID from ESP32, e.g., MAC or custom')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'

    def __str__(self):
        return f"({self.device_id})"


class SensorReading(models.Model):
    """
    Stores soil moisture readings sent from the ESP32.
    Used for real-time status and historical charts in the dashboard.
    """
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='readings')
    moisture_level = models.FloatField(help_text='Soil moisture percentage (0-100)')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Sensor Reading'
        verbose_name_plural = 'Sensor Readings'
        ordering = ['-timestamp']  

    def __str__(self):
        return f"{self.device.name}: {self.moisture_level}% at {self.timestamp}"


class PumpCommand(models.Model):
    """
    Logs pump control commands (ON/OFF) for action history in the dashboard.
    Can be triggered manually via app or automatically via backend logic.
    """
    ACTION_CHOICES = [
        ('ON', 'Turn Pump ON'),
        ('OFF', 'Turn Pump OFF'),
    ]
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='commands')
    action = models.CharField(max_length=3, choices=ACTION_CHOICES)
    triggered_by = models.CharField(max_length=20, default='manual', help_text='manual, auto, or api')
    timestamp = models.DateTimeField(default=timezone.now)
    acknowledged = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Pump Command'
        verbose_name_plural = 'Pump Commands'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.device.name}: {self.get_action_display()} at {self.timestamp}"


class CurrentStatus(models.Model):
    """
    Denormalized current status for fast dashboard reads.
    Updated via signals or API when readings/commands change.
    """
    device = models.OneToOneField(Device, on_delete=models.CASCADE, related_name='current_status')
    current_moisture = models.FloatField(default=0)
    pump_status = models.BooleanField(default=False)  # True=ON, False=OFF
    auto_mode = models.BooleanField(default=False)
    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Current Status'
        verbose_name_plural = 'Current Statuses'

    def __str__(self):
        return f"{self.device.name} Status: Moisture {self.current_moisture}%, Pump {self.pump_status} and {self.auto_mode}"