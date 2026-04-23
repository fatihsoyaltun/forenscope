from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(tf_urls)),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', include('apps.core.urls', namespace='core')),
    path('tickets/', include('apps.service.urls', namespace='service')),
    path('knowledge/', include('apps.knowledge.urls', namespace='knowledge')),
    path('account/', include('apps.accounts.urls', namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
