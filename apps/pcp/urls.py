from django.urls import path
from . import views

app_name = 'pcp'

urlpatterns = [
    path('', views.pcp_upload, name='pcp-upload'),
]