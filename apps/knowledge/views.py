from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Q
from django.http import HttpResponse, Http404, FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from .models import KnowledgeArticle, ArticleAttachment
from .forms import ArticleForm
from apps.service.models import FaultCategory


def _article_qs(user):
    qs = KnowledgeArticle.objects.select_related(
        'fault_category', 'symptom', 'source_ticket', 'author', 'approved_by'
    )
    if user.groups.filter(name='Admin').exists():
        return qs
    if user.groups.filter(name='Technician').exists():
        return qs.filter(Q(status='published') | Q(author=user))
    return qs.filter(status='published')


class ArticleListView(LoginRequiredMixin, ListView):
    template_name = 'knowledge/article_list.html'
    context_object_name = 'articles'
    paginate_by = 20

    def get_queryset(self):
        qs = _article_qs(self.request.user)
        q = self.request.GET.get('q', '').strip()
        family = self.request.GET.get('family', '')
        category = self.request.GET.get('category', '')

        if q:
            try:
                search_query = SearchQuery(q, config='turkish')
                qs = (
                    qs.filter(search_vector=search_query)
                    .annotate(rank=SearchRank('search_vector', search_query))
                    .order_by('-rank')
                )
            except Exception:
                qs = qs.filter(
                    Q(title__icontains=q) | Q(summary__icontains=q) |
                    Q(solution_body__icontains=q) | Q(tags__icontains=q)
                ).order_by('-updated_at')
        else:
            qs = qs.order_by('-updated_at')

        if family:
            qs = qs.filter(device_family=family)
        if category:
            qs = qs.filter(fault_category_id=category)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_count'] = _article_qs(self.request.user).filter(status='published').count()
        ctx['categories'] = FaultCategory.objects.filter(is_active=True)
        return ctx

    def get(self, request, *args, **kwargs):
        if request.htmx:
            self.object_list = self.get_queryset()
            ctx = self.get_context_data()
            html = render_to_string('knowledge/_article_grid.html', ctx, request=request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)


class ArticleDetailView(LoginRequiredMixin, DetailView):
    template_name = 'knowledge/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        return _article_qs(self.request.user)

    def get_object(self, queryset=None):
        obj = get_object_or_404(self.get_queryset(), slug=self.kwargs['slug'])
        KnowledgeArticle.objects.filter(pk=obj.pk).update(view_count=obj.view_count + 1)
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        article = self.object
        ctx['related_articles'] = (
            _article_qs(self.request.user)
            .filter(fault_category=article.fault_category, status='published')
            .exclude(pk=article.pk)[:4]
        )
        ctx['is_admin'] = self.request.user.groups.filter(name='Admin').exists()
        ctx['is_technician'] = self.request.user.groups.filter(name='Technician').exists()
        return ctx


class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = KnowledgeArticle
    template_name = 'knowledge/article_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.groups.filter(name='ReadOnly').exists():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        kwargs['user'] = self.request.user
        return ArticleForm(**kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        if not self.request.user.groups.filter(name='Admin').exists():
            form.instance.status = 'draft'
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'create'
        ctx['categories'] = FaultCategory.objects.filter(is_active=True)
        ctx['is_admin'] = self.request.user.groups.filter(name='Admin').exists()
        return ctx


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    model = KnowledgeArticle
    template_name = 'knowledge/article_form.html'
    slug_field = 'slug'

    def get_queryset(self):
        return _article_qs(self.request.user)

    def dispatch(self, request, *args, **kwargs):
        obj = get_object_or_404(KnowledgeArticle, slug=kwargs['slug'])
        is_admin = request.user.groups.filter(name='Admin').exists()
        if not is_admin and obj.author != request.user:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        kwargs['user'] = self.request.user
        return ArticleForm(**kwargs)

    def form_valid(self, form):
        form.instance.version = self.object.version + 1
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'edit'
        ctx['categories'] = FaultCategory.objects.filter(is_active=True)
        ctx['is_admin'] = self.request.user.groups.filter(name='Admin').exists()
        return ctx


class ArticleApproveView(LoginRequiredMixin, View):
    def post(self, request, slug):
        if not request.user.groups.filter(name='Admin').exists():
            raise Http404
        article = get_object_or_404(KnowledgeArticle, slug=slug)
        article.status = 'published'
        article.approved_by = request.user
        article.approved_at = timezone.now()
        article.save()
        messages.success(request, f'"{article.title}" yayınlandı.')
        return redirect(reverse('knowledge:article_detail', kwargs={'slug': slug}))


class ArticleArchiveView(LoginRequiredMixin, View):
    def post(self, request, slug):
        if not request.user.groups.filter(name='Admin').exists():
            raise Http404
        article = get_object_or_404(KnowledgeArticle, slug=slug)
        article.status = 'archived'
        article.save()
        messages.success(request, f'"{article.title}" arşivlendi.')
        return redirect(reverse('knowledge:article_list'))


class AttachmentDownloadView(LoginRequiredMixin, View):
    def get(self, request, pk):
        att = get_object_or_404(ArticleAttachment, pk=pk)
        get_object_or_404(_article_qs(request.user), pk=att.article_id)
        try:
            return FileResponse(att.file.open('rb'), as_attachment=True, filename=att.original_name)
        except FileNotFoundError:
            raise Http404


class AttachmentStreamView(LoginRequiredMixin, View):
    def get(self, request, pk):
        att = get_object_or_404(ArticleAttachment, pk=pk)
        get_object_or_404(_article_qs(request.user), pk=att.article_id)
        content_type = att.mime_type or 'application/octet-stream'
        try:
            return FileResponse(att.file.open('rb'), content_type=content_type)
        except FileNotFoundError:
            raise Http404
