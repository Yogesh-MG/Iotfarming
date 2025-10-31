from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from .models import User, Device, SensorReading, PumpCommand, CurrentStatus
from .serializer import (
    UserSerializer, DeviceSerializer, SensorReadingSerializer, 
    PumpCommandSerializer, 
    ReadingInputSerializer, PumpUpdateSerializer
)
from .authentication import DeviceAPIKeyAuthentication  # Custom auth for ESP API keys


class AutoModeView(APIView):
    """
    POST /api/auto-mode/ - Toggle auto mode ON/OFF by user (JWT only).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AutoModeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.filter(user=request.user, is_active=True).first()
            if not device:
                return Response({'message': 'No active device found'}, status=status.HTTP_404_NOT_FOUND)

            enabled = serializer.validated_data['enabled']
            device.is_auto_mode = enabled
            device.save()

            return Response({
                'message': f'Auto mode {"enabled" if enabled else "disabled"}',
                'is_auto_mode': enabled
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in AutoModeView: {e}")  # Debugging
            return Response({'message': 'Failed to update auto mode'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MeView(APIView):
    """
    GET /api/me/ - User profile for post-login.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StatusView(APIView):
    """
    GET /api/status/ - Dashboard status for user (JWT) or ESP poll (API key).
    - If JWT: Returns user's device status with history/actions.
    - If API key: Returns device's latest moisture, pump status, and pending commands (for ESP sync).
    Assumes one active device per user.
    """
    authentication_classes = [DeviceAPIKeyAuthentication]  # Supports both JWT and API key
    permission_classes = []  # Handled by auth classes

    def get(self, request):
        try:
            # If DeviceAPIKeyAuthentication -> request.user is a Device instance
            device = None
            is_device_request = hasattr(request.user, 'name') and not hasattr(request.user, 'username')

            if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated and hasattr(request.user, 'username'):
                # JWT Authenticated user (dashboard)
                device = Device.objects.filter(user=request.user, is_active=True).first()
            elif is_device_request:
                # API Key authenticated Device
                device = request.user

            if not device:
                return Response({'message': 'No active device found'}, status=status.HTTP_404_NOT_FOUND)

            # Ensure CurrentStatus exists
            current_status, _ = CurrentStatus.objects.get_or_create(device=device)

            latest_reading = device.readings.order_by('-timestamp').first()

            base_data = {
                'soil_moisture': latest_reading.moisture_level if latest_reading else current_status.current_moisture,
                'motor_status': current_status.pump_status,
                'is_auto_mode': device.is_auto_mode,  # New: Include auto mode status
                'timestamp': latest_reading.timestamp if latest_reading else current_status.last_updated,
                'history': SensorReadingSerializer(device.readings.order_by('-timestamp')[:10], many=True).data,
            }

            # For user (JWT): Include full actions history
            if hasattr(request.user, 'username'):  # User view
                base_data['actions'] = PumpCommandSerializer(device.commands.order_by('-timestamp')[:10], many=True).data
                return Response(base_data, status=status.HTTP_200_OK)

            # For ESP (API key): Include pending commands (e.g., unacknowledged ON/OFF)
            # Assume commands have an 'acknowledged' field; add if needed
            pending_commands = device.commands.filter(acknowledged=False).order_by('-timestamp')[:5]  # Example logic
            base_data['pending_commands'] = PumpCommandSerializer(pending_commands, many=True).data
            base_data['actions'] = []  # Or minimal for ESP

            return Response(base_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in StatusView: {e}")  # Debugging
            return Response({'message': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdatePumpView(APIView):
    """
    POST /api/update/ - Toggle pump ON/OFF by user (JWT only).
    Logs command, updates status. ESP polls via /status/ for commands.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PumpUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = Device.objects.filter(user=request.user, is_active=True).first()
            if not device:
                return Response({'message': 'No active device found'}, status=status.HTTP_404_NOT_FOUND)

            pump_state = serializer.validated_data['pump_state']
            action = 'ON' if pump_state else 'OFF'

            # Create command log (mark as unacknowledged for ESP poll)
            command = PumpCommand.objects.create(
                device=device,
                action=action,
                triggered_by='manual',
                acknowledged=False  # Add this field to model if needed
            )

            # Update current status
            current_status, _ = CurrentStatus.objects.get_or_create(device=device)
            current_status.pump_status = pump_state
            current_status.last_updated = timezone.now()
            current_status.save()

            # In production: Optional immediate push to ESP via webhook/MQTT

            return Response({
                'message': f'Pump turned {action}',
                'action': command.action,
                'timestamp': command.timestamp
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in UpdatePumpView: {e}")  # Debugging
            return Response({'message': 'Failed to update pump'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class ReadingView(APIView):
    """
    POST /api/readings/ - ESP sends moisture data (API key required).
    Updates status; optionally acknowledge commands.
    Auto-triggers pump if in auto mode.
    """
    authentication_classes = [DeviceAPIKeyAuthentication]
    permission_classes = []

    def post(self, request):
        serializer = ReadingInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            device = request.user  # From API key authentication
            moisture = serializer.validated_data['moisture']

            # Create reading
            reading = SensorReading.objects.create(
                device=device,
                moisture_level=moisture,
                timestamp=timezone.now()
            )

            # Update current status
            current_status, _ = CurrentStatus.objects.get_or_create(device=device)
            current_status.current_moisture = moisture
            current_status.last_updated = timezone.now()
            current_status.save()

            # Auto-trigger logic if enabled
            if device.is_auto_mode:
                if moisture < 30 and not current_status.pump_status:
                    # Trigger ON
                    command = PumpCommand.objects.create(
                        device=device,
                        action='ON',
                        triggered_by='auto',
                        acknowledged=False
                    )
                    current_status.pump_status = True
                    current_status.save()
                    print(f"Auto-triggered pump ON due to low moisture: {moisture}%")  # Logging
                elif moisture > 60 and current_status.pump_status:
                    # Trigger OFF
                    command = PumpCommand.objects.create(
                        device=device,
                        action='OFF',
                        triggered_by='auto',
                        acknowledged=False
                    )
                    current_status.pump_status = False
                    current_status.save()
                    print(f"Auto-triggered pump OFF due to high moisture: {moisture}%")  # Logging

            # Optional: Acknowledge pending commands on successful reading (if payload includes ack)
            if 'ack_command_ids' in serializer.validated_data:
                command_ids = serializer.validated_data['ack_command_ids']
                PumpCommand.objects.filter(id__in=command_ids, device=device).update(acknowledged=True)

            return Response({'message': 'Reading recorded', 'reading_id': reading.id}, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error in ReadingView: {e}")  # Debugging
            return Response({'message': 'Failed to record reading'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserCreateView(APIView):
    """
    POST /api/users/ - Admin creates user (no manual registration).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Check if superuser
        if not request.user.is_superuser:
            return Response({'message': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        user_data = {
            'username': data.get('username'),
            'email': data.get('email'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'password': data.get('password'),
        }

        with transaction.atomic():
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                user = user_serializer.save()
            else:
                print(user_serializer.errors)  # Debugging
                return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # Optional: Auto-create device for new user
            device_data = {
                'user': user.id,
                'name': data.get('device_name', 'Default Irrigation Device'),
                'device_id': data.get('device_id', f'device_{user.id}'),
            }
            device_serializer = DeviceSerializer(data=device_data)
            if device_serializer.is_valid():
                device = device_serializer.save()
                # Create initial current status
                CurrentStatus.objects.get_or_create(device=device)
                return Response({
                    'message': 'User and device created successfully',
                    'user_id': user.id,
                    'device_id': device.id
                }, status=status.HTTP_201_CREATED)
            else:
                raise Exception('Device creation failed')  # Triggers rollback

        return Response({'message': 'Failed to create user and device'}, status=status.HTTP_400_BAD_REQUEST)


class DeviceCreateView(APIView):
    """
    POST /api/devices/ - Admin creates device for existing user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'message': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = DeviceSerializer(data=request.data)
        if serializer.is_valid():
            device = serializer.save()
            # Create initial current status
            CurrentStatus.objects.get_or_create(device=device)
            # Generate API key if needed (assume handled in model or elsewhere)
            return Response({
                'message': 'Device created successfully',
                'device_id': device.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)