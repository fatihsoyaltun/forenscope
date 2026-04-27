from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from .forms import UserCreateForm, UserEditForm

User = get_user_model()


def admin_required(user):
    return user.groups.filter(name='Admin').exists() or user.is_superuser


class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'

    def dispatch(self, request, *args, **kwargs):
        if not admin_required(request.user):
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return User.objects.prefetch_related('groups').order_by('-date_joined')


class UserCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def dispatch(self, request, *args, **kwargs):
        if not admin_required(request.user):
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Kullanıcı oluşturuldu.')
        return super().form_valid(form)


class UserEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('accounts:user_list')

    def dispatch(self, request, *args, **kwargs):
        if not admin_required(request.user):
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, 'Kullanıcı güncellendi.')
        return super().form_valid(form)


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'accounts/password_change.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, response):
        messages.success(self.request, 'Şifreniz başarıyla güncellendi.')
        return super().form_valid(response)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mfa_active'] = self.request.user.totpdevice_set.filter(confirmed=True).exists()
        return ctx
