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
    ReadingInputSerializer, PumpUpdateSerializer, AutoModeSerializer
)
from rest_framework_simplejwt.authentication import JWTAuthentication
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

           
            current_status, _ = CurrentStatus.objects.get_or_create(device=device)
            current_status.auto_mode = enabled
            current_status.save()

            return Response({
                'message': f'Auto mode {"enabled" if enabled else "disabled"}',
                'is_auto_mode': enabled
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in AutoModeView: {e}")
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
    authentication_classes = [DeviceAPIKeyAuthentication, JWTAuthentication]  # Supports both JWT and API key
    permission_classes = []

    def get(self, request):
        try:
            device = None
            is_device_request = hasattr(request.user, 'name') and not hasattr(request.user, 'username')
            print(request.user)

            if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated and hasattr(request.user, 'username'):
                
                device = Device.objects.filter(user=request.user, is_active=True).first()
                print(device)
            elif is_device_request:
                device = request.user

            if not device:
                return Response({'message': 'No active device found'}, status=status.HTTP_404_NOT_FOUND)

            
            current_status, _ = CurrentStatus.objects.get_or_create(device=device)

            latest_reading = device.readings.order_by('-timestamp').first()

            base_data = {
                'soil_moisture': latest_reading.moisture_level if latest_reading else current_status.current_moisture,
                'motor_status': current_status.pump_status,
                'is_auto_mode': current_status.auto_mode,  
                'timestamp': latest_reading.timestamp if latest_reading else current_status.last_updated,
                'history': SensorReadingSerializer(device.readings.order_by('-timestamp')[:10], many=True).data,
            }

            
            if hasattr(request.user, 'username'):  
                base_data['actions'] = PumpCommandSerializer(device.commands.order_by('-timestamp')[:10], many=True).data
                return Response(base_data, status=status.HTTP_200_OK)

            
            pending_commands = device.commands.filter(acknowledged=False).order_by('-timestamp')[:5]  
            base_data['pending_commands'] = PumpCommandSerializer(pending_commands, many=True).data
            base_data['actions'] = []  

            return Response(base_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in StatusView: {e}")  
            return Response({'message': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class StatusViewEsp(APIView):
    """
    GET /api/status/ - Dashboard status for user (JWT) or ESP poll (API key).
    - If JWT: Returns user's device status with history/actions.
    - If API key: Returns device's latest moisture, pump status, and pending commands (for ESP sync).
    Assumes one active device per user.
    """
    authentication_classes = [DeviceAPIKeyAuthentication, JWTAuthentication]  # Supports both JWT and API key
    permission_classes = []

    def get(self, request):
        try:
            device = None
            is_device_request = hasattr(request.user, 'name') and not hasattr(request.user, 'username')
            print(request.user)

            if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated and hasattr(request.user, 'username'):
                
                device = Device.objects.filter(user=request.user, is_active=True).first()
                print(device)
            elif is_device_request:
                device = request.user

            if not device:
                return Response({'message': 'No active device found'}, status=status.HTTP_404_NOT_FOUND)

            
            current_status, _ = CurrentStatus.objects.get_or_create(device=device)

            latest_reading = device.readings.order_by('-timestamp').first()

            base_data = {
                'soil_moisture': latest_reading.moisture_level if latest_reading else current_status.current_moisture,
                'motor_status': current_status.pump_status,
                'is_auto_mode': current_status.auto_mode,  
                'timestamp': latest_reading.timestamp if latest_reading else current_status.last_updated,
            } 

            return Response(base_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error in StatusView: {e}")  
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

            
            command = PumpCommand.objects.create(
                device=device,
                action=action,
                triggered_by='manual',
                acknowledged=False  
            )

          
            current_status, _ = CurrentStatus.objects.get_or_create(device=device)
            current_status.pump_status = pump_state
            current_status.last_updated = timezone.now()
            current_status.save()


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
            device = request.user  
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
            if current_status.auto_mode:
                if moisture < 30 and not current_status.pump_status:
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
                    command = PumpCommand.objects.create(
                        device=device,
                        action='OFF',
                        triggered_by='auto',
                        acknowledged=False
                    )
                    current_status.pump_status = False
                    current_status.save()
                    print(f"Auto-triggered pump OFF due to high moisture: {moisture}%")  # Logging

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

            device_data = {
                'user': user.id,
                'name': data.get('device_name', 'Default Irrigation Device'),
                'device_id': data.get('device_id', f'device_{user.id}'),
            }
            device_serializer = DeviceSerializer(data=device_data)
            if device_serializer.is_valid():
                device = device_serializer.save()
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
            CurrentStatus.objects.get_or_create(device=device)
            return Response({
                'message': 'Device created successfully',
                'device_id': device.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)