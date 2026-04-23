from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission


class Command(BaseCommand):
    help = 'Create default groups with permissions'

    def handle(self, *args, **options):
        # --- Admin Group ---
        admin_group, _ = Group.objects.get_or_create(name='Admin')
        admin_perms = Permission.objects.filter(
            content_type__app_label__in=['service', 'knowledge', 'accounts', 'auditlog']
        )
        admin_group.permissions.set(admin_perms)
        self.stdout.write(self.style.SUCCESS('Admin group: OK'))

        # --- Technician Group ---
        tech_group, _ = Group.objects.get_or_create(name='Technician')
        tech_perms = Permission.objects.filter(
            content_type__app_label='service',
            codename__in=[
                'add_serviceticket', 'change_serviceticket', 'view_serviceticket',
                'add_attachment', 'view_attachment',
                'add_ticketcomment', 'change_ticketcomment', 'view_ticketcomment',
                'view_device', 'view_part',
                'view_faultcategory', 'view_symptom',
            ]
        )
        tech_group.permissions.set(tech_perms)
        self.stdout.write(self.style.SUCCESS('Technician group: OK'))

        # --- ReadOnly Group ---
        readonly_group, _ = Group.objects.get_or_create(name='ReadOnly')
        readonly_perms = Permission.objects.filter(
            content_type__app_label='service',
            codename__startswith='view_'
        )
        readonly_group.permissions.set(readonly_perms)
        self.stdout.write(self.style.SUCCESS('ReadOnly group: OK'))

        self.stdout.write(self.style.SUCCESS('\nAll groups created successfully.'))
