from django.urls import path
from .views import DashboardView, StatsApiView

app_name = 'core'
urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('api/stats/', StatsApiView.as_view(), name='stats_api'),
]
