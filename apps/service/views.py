from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.views import View as BaseView
from django.http import HttpResponse, Http404
from django.db.models import Q, Count
from django.utils import timezone

from auditlog.models import LogEntry
from .models import (
    ServiceTicket, Device, FaultCategory, Symptom,
    Part, Attachment, TicketComment
)
from .forms import TicketCreateForm, TicketResolveForm, AttachmentUploadForm, TicketCommentForm

User = get_user_model()


def get_user_ticket_queryset(user):
    qs = ServiceTicket.objects.select_related(
        'device', 'fault_category', 'symptom',
        'assigned_to', 'created_by'
    )
    if user.groups.filter(name='Admin').exists():
        return qs
    if user.groups.filter(name='Technician').exists():
        return qs.filter(Q(created_by=user) | Q(assigned_to=user))
    return qs


class TicketListView(LoginRequiredMixin, ListView):
    model = ServiceTicket
    template_name = 'service/ticket_list.html'
    context_object_name = 'page_obj'
    paginate_by = 25

    def get_queryset(self):
        qs = get_user_ticket_queryset(self.request.user)
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '')
        priority = self.request.GET.get('priority', '')
        family = self.request.GET.get('family', '')
        category = self.request.GET.get('category', '')

        if q:
            qs = qs.filter(
                Q(subject__icontains=q) |
                Q(code__icontains=q) |
                Q(device__serial_no__icontains=q) |
                Q(device__customer_name__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if priority:
            qs = qs.filter(priority=priority)
        if family:
            qs = qs.filter(device__family=family)
        if category:
            qs = qs.filter(fault_category_id=category)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = get_user_ticket_queryset(self.request.user)
        ctx['open_count'] = qs.exclude(status__in=['resolved', 'closed']).count()
        ctx['categories'] = FaultCategory.objects.filter(is_active=True)
        return ctx

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.htmx:
            return HttpResponse(
                response.rendered_content,
                headers={'HX-Reswap': 'innerHTML'}
            )
        return response


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = ServiceTicket
    template_name = 'service/ticket_detail.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get_object(self):
        ticket = get_object_or_404(ServiceTicket, code=self.kwargs['code'])
        user = self.request.user
        if user.groups.filter(name__in=['Admin', 'Technician', 'ReadOnly']).exists():
            return ticket
        raise Http404

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ticket = self.object
        ctx['device_tickets'] = ServiceTicket.objects.filter(
            device=ticket.device
        ).order_by('-created_at')[:6]
        ctx['comment_form'] = TicketCommentForm()
        ctx['upload_form'] = AttachmentUploadForm()
        ctx['audit_logs'] = LogEntry.objects.get_for_object(ticket).order_by('-timestamp')[:20]
        return ctx


class TicketCreateView(LoginRequiredMixin, CreateView):
    model = ServiceTicket
    form_class = TicketCreateForm
    template_name = 'service/ticket_create.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name__in=['Admin', 'Technician']).exists():
            messages.error(request, 'Bu sayfaya erişim yetkiniz yok.')
            return redirect('service:ticket_list')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = FaultCategory.objects.filter(is_active=True)
        ctx['technicians'] = User.objects.filter(
            groups__name__in=['Admin', 'Technician']
        ).distinct()
        return ctx

    def form_valid(self, form):
        serial_no = form.cleaned_data['serial_no'].upper()
        family = form.cleaned_data['device_family']
        customer = form.cleaned_data.get('customer_name', '')

        device, _ = Device.objects.get_or_create(
            serial_no=serial_no,
            defaults={'family': family, 'customer_name': customer}
        )

        ticket = form.save(commit=False)
        ticket.device = device
        ticket.created_by = self.request.user
        ticket.save()
        form.save_m2m()

        messages.success(self.request, f'Servis kaydı {ticket.code} oluşturuldu.')
        return redirect('service:ticket_detail', code=ticket.code)

    def form_invalid(self, form):
        messages.error(self.request, 'Form hataları var, lütfen kontrol edin.')
        return super().form_invalid(form)


class TicketUpdateView(LoginRequiredMixin, UpdateView):
    model = ServiceTicket
    template_name = 'service/ticket_edit.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'
    fields = ['fault_category', 'symptom', 'subject', 'description', 'priority', 'assigned_to', 'status']

    def dispatch(self, request, *args, **kwargs):
        if not request.user.has_perm('service.change_serviceticket'):
            messages.error(request, 'Bu ticket için düzenleme yetkiniz yok.')
            return redirect('service:ticket_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['fault_category'].queryset = FaultCategory.objects.filter(is_active=True)
        form.fields['symptom'].queryset = Symptom.objects.filter(is_active=True)
        form.fields['assigned_to'].queryset = User.objects.filter(
            groups__name__in=['Admin', 'Technician']
        ).distinct()
        form.fields['assigned_to'].required = False
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = FaultCategory.objects.filter(is_active=True)
        ctx['technicians'] = User.objects.filter(
            groups__name__in=['Admin', 'Technician']
        ).distinct()
        return ctx

    def get_success_url(self):
        return reverse('service:ticket_detail', kwargs={'code': self.object.code})

    def form_valid(self, form):
        messages.success(self.request, 'Ticket güncellendi.')
        return super().form_valid(form)


class TicketResolveView(LoginRequiredMixin, UpdateView):
    model = ServiceTicket
    form_class = TicketResolveForm
    template_name = 'service/ticket_resolve.html'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def dispatch(self, request, *args, **kwargs):
        ticket = get_object_or_404(ServiceTicket, code=kwargs['code'])
        user = request.user
        is_admin = user.groups.filter(name='Admin').exists()
        is_assigned = ticket.assigned_to == user
        if not (is_admin or is_assigned):
            messages.error(request, 'Bu ticket için çözüm girme yetkiniz yok.')
            return redirect('service:ticket_detail', code=kwargs['code'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['parts'] = Part.objects.filter(is_active=True)
        ctx['selected_parts'] = list(
            self.object.parts_used.values_list('id', flat=True)
        )
        return ctx

    def form_valid(self, form):
        ticket = form.save(commit=False)
        if ticket.status == 'closed' and not ticket.closed_at:
            ticket.closed_at = timezone.now()
        ticket.save()
        form.save_m2m()
        messages.success(self.request, 'Çözüm bilgileri kaydedildi.')
        return redirect('service:ticket_detail', code=ticket.code)


class AttachmentUploadView(LoginRequiredMixin, BaseView):
    def post(self, request, code):
        ticket = get_object_or_404(ServiceTicket, code=code)
        if not request.user.groups.filter(name__in=['Admin', 'Technician']).exists():
            return HttpResponse(status=403)

        form = AttachmentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES['file']
            att = form.save(commit=False)
            att.ticket = ticket
            att.original_name = f.name
            att.size_bytes = f.size
            att.uploaded_by = request.user
            att.save()
            messages.success(request, f'{f.name} yüklendi.')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])

        return redirect('service:ticket_detail', code=code)


class AttachmentDownloadView(LoginRequiredMixin, BaseView):
    def get(self, request, pk):
        att = get_object_or_404(Attachment, pk=pk)
        user = request.user
        ticket = att.ticket
        if not user.groups.filter(name='Admin').exists():
            if not user.groups.filter(name='ReadOnly').exists():
                if not (ticket.created_by == user or ticket.assigned_to == user):
                    raise Http404

        response = HttpResponse()
        response['Content-Type'] = att.mime_type or 'application/octet-stream'
        response['Content-Disposition'] = f'attachment; filename="{att.original_name}"'
        response['X-Accel-Redirect'] = f'/protected/{att.file.name}'
        return response


class TicketCommentView(LoginRequiredMixin, BaseView):
    def post(self, request, code):
        ticket = get_object_or_404(ServiceTicket, code=code)
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            if comment.is_internal:
                if not request.user.groups.filter(name__in=['Admin', 'Technician']).exists():
                    comment.is_internal = False
            comment.save()
            messages.success(request, 'Yorum eklendi.')
        else:
            messages.error(request, 'Yorum eklenemedi.')
        return redirect('service:ticket_detail', code=code)


class SymptomByCategoryView(LoginRequiredMixin, BaseView):
    """HTMX endpoint: symptom <select> options for a given category.

    ticket_create.html uses hx-get with category_id=0 as a sentinel plus
    hx-include to pass the real category as a GET query param fault_category.
    """
    def get(self, request, category_id):
        if category_id == 0:
            try:
                category_id = int(request.GET.get('fault_category', 0))
            except (ValueError, TypeError):
                category_id = 0

        symptoms = Symptom.objects.filter(
            category_id=category_id, is_active=True
        ).order_by('name')
        html = '<select name="symptom" class="fs-select" style="width:100%;">'
        html += '<option value="">— Seçin —</option>'
        for s in symptoms:
            html += f'<option value="{s.id}">{s.name}</option>'
        html += '</select>'
        return HttpResponse(html)


class DeviceLookupView(LoginRequiredMixin, BaseView):
    """HTMX endpoint: device info card by serial number."""
    def post(self, request):
        serial_no = request.POST.get('serial_no', '').strip().upper()
        if not serial_no:
            return HttpResponse('<div style="color:var(--fs-muted);font-size:11px;">Seri no girin</div>')
        try:
            device = Device.objects.get(serial_no=serial_no)
            ticket_count = device.tickets.count()
            html = f'''
            <div style="font-size:11px;line-height:1.8;">
                <div style="color:var(--fs-green);margin-bottom:4px;">✓ Cihaz bulundu</div>
                <div style="color:var(--fs-muted);">Aile: <span style="color:var(--fs-text);">{device.get_family_display()}</span></div>
                <div style="color:var(--fs-muted);">Müşteri: <span style="color:var(--fs-text);">{device.customer_name or "—"}</span></div>
                <div style="color:var(--fs-muted);">Toplam kayıt: <span style="color:var(--fs-accent);">{ticket_count}</span></div>
            </div>'''
        except Device.DoesNotExist:
            html = '<div style="color:var(--fs-yellow);font-size:11px;">Yeni cihaz — kayıt oluşturulacak</div>'
        return HttpResponse(html)


class DeviceListView(LoginRequiredMixin, ListView):
    model = Device
    template_name = 'service/device_list.html'
    context_object_name = 'devices'
    paginate_by = 25

    def get_queryset(self):
        qs = Device.objects.annotate(ticket_count=Count('tickets'))
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(
                Q(serial_no__icontains=q) |
                Q(customer_name__icontains=q) |
                Q(model_name__icontains=q)
            )
        return qs.order_by('-ticket_count')


class PartListView(LoginRequiredMixin, ListView):
    model = Part
    template_name = 'service/part_list.html'
    context_object_name = 'parts'

    def get_queryset(self):
        return Part.objects.annotate(
            usage=Count('tickets')
        ).filter(is_active=True).order_by('-usage')


class AuditLogView(LoginRequiredMixin, BaseView):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='Admin').exists():
            messages.error(request, 'Audit log sadece adminler için.')
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        from django.shortcuts import render
        logs = LogEntry.objects.select_related(
            'actor', 'content_type'
        ).order_by('-timestamp')[:200]
        return render(request, 'service/audit_log.html', {'logs': logs})
