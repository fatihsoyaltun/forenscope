from django.urls import path

from .views import (
    ArticleListView, ArticleDetailView, ArticleCreateView, ArticleUpdateView,
    ArticleApproveView, ArticleArchiveView,
    AttachmentUploadView, AttachmentDownloadView, AttachmentStreamView,
)

app_name = 'knowledge'

urlpatterns = [
    path('', ArticleListView.as_view(), name='article_list'),
    path('new/', ArticleCreateView.as_view(), name='article_create'),
    path('att/<int:pk>/download/', AttachmentDownloadView.as_view(), name='attachment_download'),
    path('att/<int:pk>/stream/', AttachmentStreamView.as_view(), name='attachment_stream'),
    path('<slug:slug>/', ArticleDetailView.as_view(), name='article_detail'),
    path('<slug:slug>/edit/', ArticleUpdateView.as_view(), name='article_edit'),
    path('<slug:slug>/approve/', ArticleApproveView.as_view(), name='article_approve'),
    path('<slug:slug>/archive/', ArticleArchiveView.as_view(), name='article_archive'),
    path('<slug:slug>/upload/', AttachmentUploadView.as_view(), name='attachment_upload'),
]
