from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['mfa_active'] = self.request.user.totpdevice_set.filter(confirmed=True).exists()
        return ctx
