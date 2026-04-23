from django.urls import path
from django.views.generic import TemplateView

app_name = 'service'

urlpatterns = [
    path('', TemplateView.as_view(template_name='service/ticket_list.html'), name='ticket_list'),
    path('new/', TemplateView.as_view(template_name='service/ticket_create.html'), name='ticket_create'),
    path('devices/', TemplateView.as_view(template_name='core/dashboard.html'), name='device_list'),
    path('parts/', TemplateView.as_view(template_name='core/dashboard.html'), name='part_list'),
    path('audit/', TemplateView.as_view(template_name='core/dashboard.html'), name='audit_log'),
    path('device-lookup/', TemplateView.as_view(template_name='core/dashboard.html'), name='device_lookup'),
    path('symptoms/<int:category_id>/', TemplateView.as_view(template_name='core/dashboard.html'), name='symptom_by_category'),
    path('att/<int:pk>/download/', TemplateView.as_view(template_name='core/dashboard.html'), name='attachment_download'),
    path('att/<int:pk>/upload/', TemplateView.as_view(template_name='core/dashboard.html'), name='attachment_upload'),
    path('<str:code>/', TemplateView.as_view(template_name='service/ticket_detail.html'), name='ticket_detail'),
    path('<str:code>/resolve/', TemplateView.as_view(template_name='service/ticket_resolve.html'), name='ticket_resolve'),
    path('<str:code>/edit/', TemplateView.as_view(template_name='service/ticket_create.html'), name='ticket_edit'),
    path('<str:code>/comment/', TemplateView.as_view(template_name='core/dashboard.html'), name='ticket_comment'),
]
