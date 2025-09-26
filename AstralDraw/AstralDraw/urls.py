# project_name/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Your app URLs
    #path('accounts/', include('django.contrib.auth.urls')),  # Django auth URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_URL)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)