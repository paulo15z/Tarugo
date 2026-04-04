# apps/integracoes/urls.py
from django.urls import path
from . import views

app_name = 'integracoes'

urlpatterns = [
    path('discrepancias/', views.dashboard_discrepancias, name='dashboard-discrepancias'),
]
