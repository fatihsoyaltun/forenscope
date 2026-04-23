from django.urls import path
from . import views

app_name = 'service'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='ticket_list'),
    path('new/', views.TicketCreateView.as_view(), name='ticket_create'),
    path('devices/', views.DeviceListView.as_view(), name='device_list'),
    path('parts/', views.PartListView.as_view(), name='part_list'),
    path('audit/', views.AuditLogView.as_view(), name='audit_log'),
    path('device-lookup/', views.DeviceLookupView.as_view(), name='device_lookup'),
    path('symptoms/<int:category_id>/', views.SymptomByCategoryView.as_view(), name='symptom_by_category'),
    path('att/<int:pk>/download/', views.AttachmentDownloadView.as_view(), name='attachment_download'),
    path('<str:code>/att/upload/', views.AttachmentUploadView.as_view(), name='attachment_upload'),
    path('<str:code>/', views.TicketDetailView.as_view(), name='ticket_detail'),
    path('<str:code>/resolve/', views.TicketResolveView.as_view(), name='ticket_resolve'),
    path('<str:code>/edit/', views.TicketUpdateView.as_view(), name='ticket_edit'),
    path('<str:code>/comment/', views.TicketCommentView.as_view(), name='ticket_comment'),
]
