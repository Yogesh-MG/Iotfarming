from django.contrib import admin
from .models import Device, SensorReading, PumpCommand, CurrentStatus
# Register your models here.


admin.site.register(Device)
admin.site.register(SensorReading)
admin.site.register(PumpCommand)
admin.site.register(CurrentStatus)