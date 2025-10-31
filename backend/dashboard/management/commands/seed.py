import random
import secrets
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from dashboard.models import Device, SensorReading, PumpCommand, CurrentStatus  # replace 'yourapp' with your app name


class Command(BaseCommand):
    help = "Seeds the database with dummy users, devices, sensor readings, and pump commands."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Deletes existing data before seeding new data.",
        )

    def handle(self, *args, **options):
        if options["fresh"]:
            self.stdout.write(self.style.WARNING("🧹 Clearing old data..."))
            PumpCommand.objects.all().delete()
            SensorReading.objects.all().delete()
            CurrentStatus.objects.all().delete()
            Device.objects.all().delete()
            User.objects.exclude(is_superuser=True).delete()
            self.stdout.write(self.style.SUCCESS("✅ Cleared old data."))

        self.stdout.write(self.style.NOTICE("🌱 Starting database seeding..."))

        # ---- SUPERUSER ----
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write(self.style.SUCCESS("✅ Created superuser: admin / admin123"))

        # ---- USERS ----
        users = []
        for i in range(3):
            user, created = User.objects.get_or_create(
                username=f"user{i+1}",
                defaults={"email": f"user{i+1}@example.com"},
            )
            if created:
                user.set_password("test1234")
                user.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Created user: {user.username}"))
            users.append(user)

        # ---- DEVICES ----
        devices = []
        for i, user in enumerate(users, start=1):
            device, created = Device.objects.get_or_create(
                device_id=f"ESP32_{i:03d}",
                defaults={
                    "user": user,
                    "name": f"Smart Irrigation Device {i}",
                    "api_key": secrets.token_hex(32),
                    "is_active": True,
                },
            )
            devices.append(device)
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Created device for {user.username}: {device.device_id}"))

        # ---- SENSOR READINGS ----
        for device in devices:
            for j in range(10):  # 10 readings per device
                SensorReading.objects.create(
                    device=device,
                    moisture_level=random.uniform(20.0, 80.0),
                    timestamp=timezone.now() - timedelta(minutes=j * 10),
                )
            self.stdout.write(self.style.SUCCESS(f"📊 Added 10 readings for {device.device_id}"))

        # ---- PUMP COMMANDS ----
        for device in devices:
            for j in range(3):  # few ON/OFF commands
                action = random.choice(["ON", "OFF"])
                PumpCommand.objects.create(
                    device=device,
                    action=action,
                    triggered_by=random.choice(["manual", "auto"]),
                    timestamp=timezone.now() - timedelta(hours=j),
                )
            self.stdout.write(self.style.SUCCESS(f"⚙️ Added pump commands for {device.device_id}"))

        # ---- CURRENT STATUS ----
        for device in devices:
            last_reading = device.readings.order_by("-timestamp").first()
            last_command = device.commands.order_by("-timestamp").first()

            CurrentStatus.objects.update_or_create(
                device=device,
                defaults={
                    "current_moisture": last_reading.moisture_level if last_reading else 50.0,
                    "pump_status": True if (last_command and last_command.action == "ON") else False,
                    "last_updated": timezone.now(),
                },
            )
            self.stdout.write(self.style.SUCCESS(f"🟢 Updated CurrentStatus for {device.device_id}"))

        self.stdout.write(self.style.SUCCESS("🌾 Seeding complete!"))
