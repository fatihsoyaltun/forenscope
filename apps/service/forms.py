import magic
from django import forms
from django.contrib.auth import get_user_model
from .models import ServiceTicket, Attachment, TicketComment, Device, FaultCategory, Symptom, Part

User = get_user_model()

ALLOWED_MIME_TYPES = [
    'video/mp4', 'video/quicktime', 'video/x-msvideo',
    'image/jpeg', 'image/png', 'image/webp',
    'application/pdf',
    'text/plain',
]

MAX_SIZE = {
    'video': 500 * 1024 * 1024,
    'photo': 50 * 1024 * 1024,
    'pdf':   50 * 1024 * 1024,
    'log':   10 * 1024 * 1024,
}


class TicketCreateForm(forms.ModelForm):
    serial_no = forms.CharField(
        max_length=64,
        label='Cihaz Seri No',
        help_text='Mevcut seri no girin veya yeni cihaz otomatik oluşturulur'
    )
    device_family = forms.ChoiceField(
        choices=[('', '— Seçin —')] + list(Device._meta.get_field('family').choices),
        label='Cihaz Ailesi'
    )
    customer_name = forms.CharField(max_length=256, required=False, label='Müşteri Adı')

    class Meta:
        model = ServiceTicket
        fields = ['fault_category', 'symptom', 'subject', 'description', 'priority', 'assigned_to']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fault_category'].queryset = FaultCategory.objects.filter(is_active=True)
        self.fields['symptom'].queryset = Symptom.objects.none()
        self.fields['assigned_to'].queryset = User.objects.filter(
            groups__name__in=['Admin', 'Technician']
        ).distinct()
        self.fields['assigned_to'].required = False

        if 'fault_category' in self.data:
            try:
                cat_id = int(self.data.get('fault_category'))
                self.fields['symptom'].queryset = Symptom.objects.filter(
                    category_id=cat_id, is_active=True
                )
            except (ValueError, TypeError):
                pass

    def clean_serial_no(self):
        return self.cleaned_data['serial_no'].strip().upper()


class TicketResolveForm(forms.ModelForm):
    class Meta:
        model = ServiceTicket
        fields = [
            'root_cause', 'resolution_steps', 'parts_used',
            'verification_passed', 'verification_notes', 'status'
        ]
        widgets = {
            'root_cause': forms.Textarea(attrs={'rows': 3}),
            'resolution_steps': forms.Textarea(attrs={'rows': 6}),
            'verification_notes': forms.Textarea(attrs={'rows': 2}),
            'parts_used': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parts_used'].queryset = Part.objects.filter(is_active=True)
        self.fields['status'].choices = [
            ('investigating', 'İnceleniyor'),
            ('waiting_part', 'Parça Bekleniyor'),
            ('in_progress', 'İşlemde'),
            ('resolved', 'Çözüldü'),
            ('closed', 'Kapatıldı'),
        ]


class AttachmentUploadForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file', 'kind', 'title']

    def clean_file(self):
        f = self.cleaned_data['file']
        mime = magic.from_buffer(f.read(2048), mime=True)
        f.seek(0)
        if mime not in ALLOWED_MIME_TYPES:
            raise forms.ValidationError(f'İzin verilmeyen dosya tipi: {mime}')
        kind = self.data.get('kind', 'photo')
        max_size = MAX_SIZE.get(kind, MAX_SIZE['photo'])
        if f.size > max_size:
            mb = max_size // (1024 * 1024)
            raise forms.ValidationError(f'Dosya çok büyük. Maksimum {mb}MB.')
        return f


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ['body', 'is_internal']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 3}),
        }
