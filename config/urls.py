from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('apps.core.urls', namespace='core')),
    path('tickets/', include('apps.service.urls', namespace='service')),
    path('knowledge/', include('apps.knowledge.urls', namespace='knowledge')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
