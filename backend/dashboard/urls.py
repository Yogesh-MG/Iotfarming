from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.MeView.as_view(), name='me'),
    path('status/', views.StatusView.as_view(), name='status'),
    path('status/esp/', views.StatusViewEsp.as_view(), name='status-esp'),
    path('update/', views.UpdatePumpView.as_view(), name='update_pump'),
    path('readings/', views.ReadingView.as_view(), name='readings'),
    path('auto/', views.AutoModeView.as_view(), name='auto_mode'),  # New
    path('users/', views.UserCreateView.as_view(), name='create_user'),
    path('devices/', views.DeviceCreateView.as_view(), name='create_device'),
]