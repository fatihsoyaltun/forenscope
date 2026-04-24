import json
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.service.models import ServiceTicket, Device, Part


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        if user.groups.filter(name='Admin').exists():
            qs = ServiceTicket.objects.all()
        elif user.groups.filter(name='Technician').exists():
            qs = ServiceTicket.objects.filter(
                Q(created_by=user) | Q(assigned_to=user)
            )
        else:
            qs = ServiceTicket.objects.all()

        # Stat cards
        ctx['total_tickets'] = qs.count()
        ctx['open_tickets'] = qs.exclude(status__in=['resolved', 'closed']).count()
        ctx['closed_tickets'] = qs.filter(status__in=['resolved', 'closed']).count()
        ctx['critical_tickets'] = qs.filter(
            priority__in=['high', 'critical']
        ).exclude(status__in=['resolved', 'closed']).count()

        # Last 7 days bar chart
        today = timezone.now().date()
        daily_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            count = qs.filter(created_at__date=day).count()
            daily_data.append({'date': day.strftime('%d.%m'), 'count': count})
        ctx['daily_data'] = json.dumps(daily_data)

        # Status distribution for donut chart
        status_map = {
            'new': 'Yeni',
            'investigating': 'İnceleniyor',
            'waiting_part': 'Parça Bekl.',
            'in_progress': 'İşlemde',
            'resolved': 'Çözüldü',
            'closed': 'Kapatıldı',
        }
        status_raw = list(qs.values('status').annotate(count=Count('id')))
        ctx['status_data'] = status_raw
        ctx['status_data_json'] = json.dumps([
            {'label': status_map.get(s['status'], s['status']), 'count': s['count']}
            for s in status_raw
        ])

        # Recent tickets
        ctx['recent_tickets'] = qs.select_related(
            'device', 'fault_category', 'assigned_to'
        ).order_by('-created_at')[:10]

        # Top parts used in resolved tickets
        parts = list(
            Part.objects.annotate(usage=Count('tickets'))
            .filter(usage__gt=0)
            .order_by('-usage')[:6]
        )
        if parts:
            max_usage = parts[0].usage
            for p in parts:
                p.usage_pct = int((p.usage / max_usage) * 100)
        ctx['top_parts'] = parts

        # Device family breakdown
        ctx['family_data'] = (
            Device.objects.values('family')
            .annotate(ticket_count=Count('tickets'))
            .order_by('-ticket_count')
        )

        return ctx


class StatsApiView(LoginRequiredMixin, View):
    def get(self, request):
        qs = ServiceTicket.objects.all()
        return JsonResponse({
            'total': qs.count(),
            'open': qs.exclude(status__in=['resolved', 'closed']).count(),
            'critical': qs.filter(
                priority__in=['high', 'critical']
            ).exclude(status__in=['resolved', 'closed']).count(),
        })
