from django.urls import path, include
from .views_scanner import BipagemScannerView

urlpatterns = [
    # Scanner interface
    path('scanner/', BipagemScannerView.as_view(), name='scanner'),
    
    # API endpoints (already included in config/urls.py)
]
