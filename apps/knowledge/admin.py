from django.contrib import admin

from .models import KnowledgeArticle, ArticleAttachment


class ArticleAttachmentInline(admin.TabularInline):
    model = ArticleAttachment
    extra = 0
    readonly_fields = ('original_name', 'size_bytes', 'mime_type', 'uploaded_by', 'uploaded_at')


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'device_family', 'fault_category', 'status', 'version', 'view_count', 'author', 'updated_at')
    list_filter = ('status', 'device_family', 'fault_category')
    search_fields = ('title', 'summary', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('view_count', 'created_at', 'updated_at', 'approved_at')
    inlines = [ArticleAttachmentInline]


@admin.register(ArticleAttachment)
class ArticleAttachmentAdmin(admin.ModelAdmin):
    list_display = ('original_name', 'article', 'kind', 'size_bytes', 'uploaded_by', 'uploaded_at')
    list_filter = ('kind',)
    readonly_fields = ('uploaded_at',)
