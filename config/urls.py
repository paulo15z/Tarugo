from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('estoque/', include('apps.estoque.urls')),          # views de template (front)
    path('api/estoque/', include('apps.estoque.api.urls')),  # DRF (API)
    path('pcp/', include('apps.pcp.urls')),
]
