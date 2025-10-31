from rest_framework import authentication, exceptions
from .models import Device

class DeviceAPIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = request.headers.get('X-API-KEY')
        if not api_key:
            return None  # No header, fallback to default auth
        
        try:
            device = Device.objects.get(api_key=api_key)
        except Device.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API Key')

        return (device, None)
