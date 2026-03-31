from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('estoque/', include('apps.estoque.urls')),
    path('api/estoque/', include('apps.estoque.api.urls')),
    path('pcp/', include('apps.pcp.urls')),
]

# Serve arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)