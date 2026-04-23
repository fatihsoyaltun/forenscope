import datetime
from django.db import models
from django.conf import settings
from auditlog.registry import auditlog
from simple_history.models import HistoricalRecords


DEVICE_FAMILY = [
    ('4K', '4K Kamera'),
    ('8K', '8K Kamera'),
    ('TZOOM', 'T-Zoom'),
    ('SSFORCE', 'SuperSpectral Force'),
    ('OTHER', 'Diğer'),
]

PRIORITY = [
    ('low', 'Düşük'),
    ('normal', 'Normal'),
    ('high', 'Yüksek'),
    ('critical', 'Kritik'),
]

STATUS = [
    ('new', 'Yeni'),
    ('investigating', 'İnceleniyor'),
    ('waiting_part', 'Parça Bekleniyor'),
    ('in_progress', 'İşlemde'),
    ('resolved', 'Çözüldü'),
    ('closed', 'Kapatıldı'),
]

ATTACHMENT_KIND = [
    ('video', 'Video'),
    ('photo', 'Fotoğraf'),
    ('pdf', 'PDF'),
    ('log', 'Log'),
]


class FaultCategory(models.Model):
    name = models.CharField(max_length=64, unique=True, verbose_name='Kategori')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')

    class Meta:
        verbose_name = 'Arıza Kategorisi'
        verbose_name_plural = 'Arıza Kategorileri'
        ordering = ['name']

    def __str__(self):
        return self.name


class Symptom(models.Model):
    category = models.ForeignKey(
        FaultCategory, on_delete=models.PROTECT,
        related_name='symptoms', verbose_name='Kategori'
    )
    name = models.CharField(max_length=128, verbose_name='Belirti')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')

    class Meta:
        verbose_name = 'Belirti'
        verbose_name_plural = 'Belirtiler'
        unique_together = [('category', 'name')]
        ordering = ['category', 'name']

    def __str__(self):
        return f'{self.category.name} → {self.name}'


class Part(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='Parça Kodu')
    name = models.CharField(max_length=256, verbose_name='Parça Adı')
    description = models.TextField(blank=True, verbose_name='Açıklama')
    is_active = models.BooleanField(default=True, verbose_name='Aktif')

    class Meta:
        verbose_name = 'Parça'
        verbose_name_plural = 'Parçalar'
        ordering = ['name']

    def __str__(self):
        return f'{self.code} — {self.name}'


class Device(models.Model):
    serial_no = models.CharField(
        max_length=64, unique=True, db_index=True, verbose_name='Seri No'
    )
    family = models.CharField(
        max_length=32, choices=DEVICE_FAMILY, verbose_name='Cihaz Ailesi'
    )
    model_name = models.CharField(max_length=128, blank=True, verbose_name='Model Adı')
    customer_name = models.CharField(max_length=256, blank=True, verbose_name='Müşteri Adı')
    customer_contact = models.CharField(max_length=256, blank=True, verbose_name='Müşteri İletişim')
    notes = models.TextField(blank=True, verbose_name='Notlar')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncelleme')

    class Meta:
        verbose_name = 'Cihaz'
        verbose_name_plural = 'Cihazlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.serial_no} — {self.get_family_display()}'


class ServiceTicket(models.Model):
    code = models.CharField(
        max_length=16, unique=True, db_index=True,
        editable=False, verbose_name='Servis Kodu'
    )
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT,
        related_name='tickets', verbose_name='Cihaz'
    )
    fault_category = models.ForeignKey(
        FaultCategory, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='tickets', verbose_name='Arıza Kategorisi'
    )
    symptom = models.ForeignKey(
        Symptom, on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='tickets', verbose_name='Belirti'
    )
    subject = models.CharField(max_length=256, verbose_name='Konu')
    description = models.TextField(verbose_name='Açıklama')
    root_cause = models.TextField(blank=True, verbose_name='Kök Neden')
    resolution_steps = models.TextField(blank=True, verbose_name='Çözüm Adımları')
    parts_used = models.ManyToManyField(
        Part, blank=True,
        related_name='tickets', verbose_name='Kullanılan Parçalar'
    )
    verification_passed = models.BooleanField(
        null=True, blank=True, verbose_name='Doğrulama Geçti'
    )
    verification_notes = models.TextField(blank=True, verbose_name='Doğrulama Notları')
    priority = models.CharField(
        max_length=16, choices=PRIORITY, default='normal', verbose_name='Öncelik'
    )
    status = models.CharField(
        max_length=32, choices=STATUS, default='new', verbose_name='Durum'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tickets',
        verbose_name='Atanan Kişi'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_tickets',
        verbose_name='Oluşturan'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncelleme')
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name='Kapatılma')

    history = HistoricalRecords()

    class Meta:
        verbose_name = 'Servis Kaydı'
        verbose_name_plural = 'Servis Kayıtları'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.code:
            year = datetime.datetime.now().year
            last = ServiceTicket.objects.filter(
                code__startswith=f'FS-{year}-'
            ).count()
            self.code = f'FS-{year}-{last + 1:04d}'
        if self.status == 'closed' and not self.closed_at:
            from django.utils import timezone
            self.closed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} — {self.subject}'


def attachment_upload_path(instance, filename):
    ticket = instance.ticket
    year = ticket.created_at.year if ticket.created_at else datetime.datetime.now().year
    month = ticket.created_at.month if ticket.created_at else datetime.datetime.now().month
    return f'tickets/{year}/{month:02d}/{ticket.code}/{filename}'


class Attachment(models.Model):
    ticket = models.ForeignKey(
        ServiceTicket, on_delete=models.CASCADE,
        related_name='attachments', verbose_name='Servis Kaydı'
    )
    file = models.FileField(upload_to=attachment_upload_path, verbose_name='Dosya')
    kind = models.CharField(
        max_length=16, choices=ATTACHMENT_KIND, verbose_name='Tür'
    )
    title = models.CharField(max_length=256, blank=True, verbose_name='Başlık')
    original_name = models.CharField(max_length=256, verbose_name='Orijinal Dosya Adı')
    size_bytes = models.BigIntegerField(verbose_name='Boyut (byte)')
    mime_type = models.CharField(max_length=128, blank=True, verbose_name='MIME Tipi')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Yükleyen'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Yüklenme Zamanı')

    class Meta:
        verbose_name = 'Ek Dosya'
        verbose_name_plural = 'Ek Dosyalar'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f'{self.original_name} ({self.ticket.code})'


class TicketComment(models.Model):
    ticket = models.ForeignKey(
        ServiceTicket, on_delete=models.CASCADE,
        related_name='comments', verbose_name='Servis Kaydı'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name='Yazar'
    )
    body = models.TextField(verbose_name='Yorum')
    is_internal = models.BooleanField(default=False, verbose_name='Dahili Yorum')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Oluşturulma')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Güncelleme')

    class Meta:
        verbose_name = 'Yorum'
        verbose_name_plural = 'Yorumlar'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.ticket.code} — {self.author} — {self.created_at:%d.%m.%Y}'


auditlog.register(ServiceTicket)
auditlog.register(Attachment)
auditlog.register(Device)
