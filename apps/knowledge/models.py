import datetime
import uuid

from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify

from auditlog.registry import auditlog
from simple_history.models import HistoricalRecords

from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.contrib.postgres.indexes import GinIndex

from apps.service.models import DEVICE_FAMILY, FaultCategory, Symptom, ServiceTicket


ARTICLE_STATUS = [
    ('draft', 'Taslak'),
    ('review', 'İncelemede'),
    ('published', 'Yayında'),
    ('archived', 'Arşiv'),
]

ARTICLE_ATTACHMENT_KIND = [
    ('video', 'Video'),
    ('photo', 'Fotoğraf'),
    ('pdf', 'PDF'),
    ('log', 'Log'),
]


class KnowledgeArticle(models.Model):
    title = models.CharField(max_length=256, verbose_name='Başlık')
    slug = models.SlugField(max_length=280, unique=True, db_index=True, verbose_name='Slug')
    summary = models.TextField(verbose_name='Özet')
    solution_body = models.TextField(verbose_name='Çözüm Rehberi')
    verification_checklist = models.TextField(blank=True, verbose_name='Doğrulama Listesi')

    device_family = models.CharField(
        max_length=32, choices=DEVICE_FAMILY, verbose_name='Cihaz Ailesi',
    )
    fault_category = models.ForeignKey(
        FaultCategory, on_delete=models.PROTECT,
        related_name='articles', verbose_name='Arıza Kategorisi',
    )
    symptom = models.ForeignKey(
        Symptom, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='articles', verbose_name='Belirti',
    )
    source_ticket = models.ForeignKey(
        ServiceTicket, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='articles', verbose_name='Kaynak Ticket',
    )

    tags = models.CharField(max_length=256, blank=True, verbose_name='Etiketler')
    status = models.CharField(
        max_length=16, choices=ARTICLE_STATUS, default='draft', verbose_name='Durum',
    )
    version = models.PositiveIntegerField(default=1, verbose_name='Versiyon')
    view_count = models.PositiveIntegerField(default=0, verbose_name='Görüntülenme')

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='authored_articles', verbose_name='Yazar',
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_articles', verbose_name='Onaylayan',
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Onay Zamanı')

    search_vector = SearchVectorField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncelleme')

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Makale'
        verbose_name_plural = 'Makaleler'
        ordering = ['-updated_at']
        indexes = [
            GinIndex(fields=['search_vector'], name='knowledge_search_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title, allow_unicode=False) or uuid.uuid4().hex[:8]
            slug, n = base, 1
            while KnowledgeArticle.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug, n = f'{base}-{n}', n + 1
            self.slug = slug
        super().save(*args, **kwargs)
        KnowledgeArticle.objects.filter(pk=self.pk).update(
            search_vector=(
                SearchVector('title', weight='A') +
                SearchVector('summary', weight='B') +
                SearchVector('solution_body', weight='C') +
                SearchVector('tags', weight='B')
            )
        )

    def get_absolute_url(self):
        return reverse('knowledge:article_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.title


def article_attachment_upload_path(instance, filename):
    year = (
        instance.article.created_at.year
        if instance.article_id and instance.article.created_at
        else datetime.datetime.now().year
    )
    return f'knowledge/{year}/{instance.article.slug}/{filename}'


class ArticleAttachment(models.Model):
    article = models.ForeignKey(
        KnowledgeArticle, on_delete=models.CASCADE,
        related_name='attachments', verbose_name='Makale',
    )
    file = models.FileField(upload_to=article_attachment_upload_path, verbose_name='Dosya')
    kind = models.CharField(
        max_length=16, choices=ARTICLE_ATTACHMENT_KIND, verbose_name='Tür',
    )
    title = models.CharField(max_length=256, blank=True, verbose_name='Başlık')
    original_name = models.CharField(max_length=256, verbose_name='Orijinal Dosya Adı')
    size_bytes = models.BigIntegerField(verbose_name='Boyut (byte)')
    mime_type = models.CharField(max_length=128, blank=True, verbose_name='MIME Tipi')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        verbose_name='Yükleyen',
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Yüklenme')

    class Meta:
        verbose_name = 'Ek Dosya'
        verbose_name_plural = 'Ek Dosyalar'
        ordering = ['uploaded_at']

    def __str__(self):
        return f'{self.original_name} ({self.article.slug})'


auditlog.register(KnowledgeArticle)
