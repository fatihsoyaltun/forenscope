from django import forms

from .models import KnowledgeArticle, ArticleAttachment, ARTICLE_ATTACHMENT_KIND
from apps.service.models import FaultCategory, Symptom

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

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


class ArticleForm(forms.ModelForm):
    class Meta:
        model = KnowledgeArticle
        fields = [
            'title', 'summary', 'device_family', 'fault_category', 'symptom',
            'source_ticket', 'solution_body', 'verification_checklist', 'tags', 'status',
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fault_category'].queryset = FaultCategory.objects.filter(is_active=True)
        self.fields['symptom'].queryset = Symptom.objects.filter(is_active=True)
        self.fields['symptom'].required = False
        self.fields['source_ticket'].required = False
        self.fields['verification_checklist'].required = False
        self.fields['tags'].required = False
        if user and not user.groups.filter(name='Admin').exists():
            self.fields.pop('status')


class ArticleAttachmentUploadForm(forms.ModelForm):
    class Meta:
        model = ArticleAttachment
        fields = ['file', 'kind', 'title']

    def clean_file(self):
        f = self.cleaned_data['file']
        if MAGIC_AVAILABLE:
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
