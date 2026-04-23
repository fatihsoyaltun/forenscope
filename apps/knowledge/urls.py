from django.urls import path
from django.views.generic import TemplateView

app_name = 'knowledge'

urlpatterns = [
    path('', TemplateView.as_view(template_name='knowledge/article_list.html'), name='article_list'),
    path('new/', TemplateView.as_view(template_name='knowledge/article_list.html'), name='article_create'),
    path('<slug:slug>/', TemplateView.as_view(template_name='knowledge/article_detail.html'), name='article_detail'),
    path('<slug:slug>/edit/', TemplateView.as_view(template_name='knowledge/article_detail.html'), name='article_edit'),
    path('<slug:slug>/approve/', TemplateView.as_view(template_name='knowledge/article_detail.html'), name='article_approve'),
    path('<slug:slug>/archive/', TemplateView.as_view(template_name='knowledge/article_detail.html'), name='article_archive'),
    path('att/<int:pk>/download/', TemplateView.as_view(template_name='knowledge/article_list.html'), name='attachment_download'),
    path('att/<int:pk>/stream/', TemplateView.as_view(template_name='knowledge/article_list.html'), name='attachment_stream'),
]
