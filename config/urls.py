from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.contrib.auth import views as auth_views
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticação
    path('login/',  auth_views.LoginView.as_view(),  name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Apps
    path('estoque/', include('apps.estoque.urls')),
    path('api/estoque/', include('apps.estoque.api.urls')),
    path('pcp/', include('apps.pcp.urls')),
    
    # Bipagem
    path('bipagem/', include('apps.bipagem.urls')),
    path('api/bipagem/', include('apps.bipagem.api.urls')),

    # Integrações (Gêmeo Digital)
    path('integracoes/', include('apps.integracoes.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
