from django import forms

from .models import KnowledgeArticle, ARTICLE_STATUS
from apps.service.models import FaultCategory, Symptom


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
        # Technicians cannot set status — enforced in view
        if user and not user.groups.filter(name='Admin').exists():
            self.fields.pop('status')
