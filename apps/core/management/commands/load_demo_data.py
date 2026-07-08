from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.knowledge.models import KnowledgeArticle
from apps.service.models import (
    Device,
    FaultCategory,
    Part,
    ServiceTicket,
    Symptom,
    TicketComment,
)


class Command(BaseCommand):
    help = 'Create realistic demo data for the ForenScope service dashboard.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-demo',
            action='store_true',
            help='Delete previously generated demo records before creating fresh data.',
        )

    def handle(self, *args, **options):
        User = get_user_model()

        if options['reset_demo']:
            ServiceTicket.objects.filter(code__startswith='FS-').delete()
            KnowledgeArticle.objects.filter(tags__icontains='demo').delete()
            Device.objects.filter(serial_no__startswith='DEMO-').delete()
            Part.objects.filter(code__startswith='DEMO-').delete()
            Symptom.objects.filter(description__icontains='demo').delete()
            FaultCategory.objects.filter(description__icontains='demo').delete()
            User.objects.filter(username__in=['tech.ali', 'tech.zeynep', 'service.manager']).delete()

        admin_group, _ = Group.objects.get_or_create(name='Admin')
        technician_group, _ = Group.objects.get_or_create(name='Technician')

        admin = User.objects.filter(username='admin').first()
        if not admin:
            admin = User.objects.create_superuser(
                username='admin',
                email='soyaltunfatih@gmail.com',
                password='Admin12345!',
            )
        admin.groups.add(admin_group)

        manager, _ = User.objects.update_or_create(
            username='service.manager',
            defaults={
                'email': 'service.manager@forenscope.demo',
                'first_name': 'Servis',
                'last_name': 'Yöneticisi',
                'department': 'Technical Service',
                'is_staff': True,
                'is_active': True,
            },
        )
        manager.set_password('Demo12345!')
        manager.save()
        manager.groups.add(admin_group)

        technicians = []
        for username, first, last in [
            ('tech.ali', 'Ali', 'Kaya'),
            ('tech.zeynep', 'Zeynep', 'Demir'),
        ]:
            user, _ = User.objects.update_or_create(
                username=username,
                defaults={
                    'email': f'{username}@forenscope.demo',
                    'first_name': first,
                    'last_name': last,
                    'department': 'Technical Service',
                    'is_staff': True,
                    'is_active': True,
                },
            )
            user.set_password('Demo12345!')
            user.save()
            user.groups.add(technician_group)
            technicians.append(user)

        category_data = [
            ('Görüntü / Kamera', 'demo - Kamera, lens, görüntü ve odak kaynaklı arızalar'),
            ('Işık Kaynağı / Spektral', 'demo - UV, IR, beyaz ışık, filtre ve LED modülü sorunları'),
            ('Batarya / Güç', 'demo - Batarya, şarj, güç adaptörü ve açılmama şikayetleri'),
            ('Yazılım / Bağlantı', 'demo - Uygulama, firmware, Wi-Fi/USB/HDMI ve veri aktarımı sorunları'),
            ('Mekanik / Aksesuar', 'demo - Kasa, darkroom, kablo, taşıma çantası ve aksesuar sorunları'),
        ]
        categories = {}
        for name, description in category_data:
            categories[name], _ = FaultCategory.objects.update_or_create(
                name=name,
                defaults={'description': description, 'is_active': True},
            )

        symptom_map = {
            'Görüntü / Kamera': [
                'Odak tutmuyor', 'Görüntüde kararma', 'Canlı görüntü donuyor', 'Lens çizik / kirli'
            ],
            'Işık Kaynağı / Spektral': [
                'UV LED yanmıyor', 'IR modunda düşük parlaklık', 'Filtre değişiminden sonra görüntü yok', 'Spektral renk sapması'
            ],
            'Batarya / Güç': [
                'Cihaz açılmıyor', 'Şarj almıyor', 'Batarya hızlı bitiyor', 'Adaptör uyarısı'
            ],
            'Yazılım / Bağlantı': [
                'USB bağlantısı kopuyor', 'HDMI görüntü vermiyor', 'Firmware güncelleme başarısız', 'Uygulama cihazı görmüyor'
            ],
            'Mekanik / Aksesuar': [
                'Darkroom kapağı oturmuyor', 'Askı bağlantısı gevşek', 'Case menteşe sorunu', 'Kablo temassızlık yapıyor'
            ],
        }
        symptoms = {}
        for category_name, names in symptom_map.items():
            for name in names:
                symptom, _ = Symptom.objects.update_or_create(
                    category=categories[category_name],
                    name=name,
                    defaults={'description': f'demo - {name} belirtisi', 'is_active': True},
                )
                symptoms[name] = symptom

        part_data = [
            ('DEMO-BAT-518WH', 'ForenScope 51.8 Wh Changeable Lithium-ion Battery'),
            ('DEMO-CHG-65W', '65 Watt Fast Charger'),
            ('DEMO-USB-C-30', 'USB-C / USB 3.0 Data Cable'),
            ('DEMO-HDMI-MINI', 'Mini HDMI Cable'),
            ('DEMO-LED-UV365', '365 nm UV LED Module'),
            ('DEMO-LED-IR850', '850 nm IR LED Module'),
            ('DEMO-LENS-MACRO', 'SuperSpectral Macro-Micro Lens'),
            ('DEMO-DARKROOM', 'Illuminated Darkroom Assembly'),
            ('DEMO-FILTER-SET', 'Filter Holder / Filter Set'),
            ('DEMO-CASE-HINGE', 'Protect Army Case Hinge Set'),
            ('DEMO-STRAP', 'ForenScope Leather Strap'),
        ]
        parts = []
        for code, name in part_data:
            part, _ = Part.objects.update_or_create(
                code=code,
                defaults={'name': name, 'description': f'demo - {name}', 'is_active': True},
            )
            parts.append(part)

        device_data = [
            ('DEMO-4K-24001', '4K', 'ForenScope 4K Plus', 'İstanbul Emniyet Kriminal', 'teknik@istanbul.demo'),
            ('DEMO-8K-24002', '8K', 'ForenScope 8K Pro', 'Ankara Jandarma Kriminal', 'ankara.lab@demo'),
            ('DEMO-TZ-24003', 'TZOOM', 'T-Zoom Mobile Lab', 'İzmir Olay Yeri İnceleme', 'izmir.oyi@demo'),
            ('DEMO-SSF-24004', 'SSFORCE', 'SuperSpectral Force', 'Stockholm Forensic Unit', 'stockholm.lab@demo'),
            ('DEMO-SSF-24005', 'SSFORCE', 'SuperSpectral Force', 'Dubai Police Lab', 'dubai.lab@demo'),
            ('DEMO-8K-24006', '8K', 'ForenScope 8K Ultra', 'ForenScope Demo Lab', 'demo@forenscope.demo'),
            ('DEMO-4K-24007', '4K', 'ForenScope 4K Field Kit', 'Adana Kriminal', 'adana.lab@demo'),
            ('DEMO-TZ-24008', 'TZOOM', 'T-Zoom Kit', 'Berlin Crime Scene Unit', 'berlin.lab@demo'),
        ]
        devices = []
        for serial, family, model, customer, contact in device_data:
            device, _ = Device.objects.update_or_create(
                serial_no=serial,
                defaults={
                    'family': family,
                    'model_name': model,
                    'customer_name': customer,
                    'customer_contact': contact,
                    'notes': 'demo - cihaz demo veri seti için oluşturuldu',
                },
            )
            devices.append(device)

        ticket_data = [
            ('SuperSpectral Force UV modunda görüntü kararıyor', 'Işık Kaynağı / Spektral', 'UV LED yanmıyor', 'critical', 'new', 0, [4, 8]),
            ('8K Pro cihazda HDMI çıkışı görüntü vermiyor', 'Yazılım / Bağlantı', 'HDMI görüntü vermiyor', 'high', 'investigating', 1, [3]),
            ('4K Plus batarya yüzde 30 seviyesinde kapanıyor', 'Batarya / Güç', 'Batarya hızlı bitiyor', 'normal', 'waiting_part', 2, [0]),
            ('T-Zoom uygulama cihazı USB üzerinden görmüyor', 'Yazılım / Bağlantı', 'Uygulama cihazı görmüyor', 'high', 'in_progress', 3, [2]),
            ('Macro-Micro lens odak tutmuyor', 'Görüntü / Kamera', 'Odak tutmuyor', 'normal', 'resolved', 4, [6]),
            ('Darkroom kapağı sahada tam kapanmıyor', 'Mekanik / Aksesuar', 'Darkroom kapağı oturmuyor', 'low', 'closed', 5, [7]),
            ('IR modunda parlaklık düşük ve görüntü noise üretiyor', 'Işık Kaynağı / Spektral', 'IR modunda düşük parlaklık', 'high', 'resolved', 6, [5, 8]),
            ('Protect Army Case menteşesi gevşemiş', 'Mekanik / Aksesuar', 'Case menteşe sorunu', 'low', 'closed', 7, [9]),
            ('Firmware güncelleme sonrası canlı görüntü donuyor', 'Yazılım / Bağlantı', 'Firmware güncelleme başarısız', 'critical', 'in_progress', 0, [2]),
            ('Filtre değişiminden sonra beyaz ışıkta görüntü yok', 'Işık Kaynağı / Spektral', 'Filtre değişiminden sonra görüntü yok', 'critical', 'investigating', 1, [8]),
            ('Şarj adaptörü bağlıyken cihaz kesik kesik akım çekiyor', 'Batarya / Güç', 'Şarj almıyor', 'high', 'waiting_part', 2, [1, 0]),
            ('Lens temizliği sonrası görüntüde sisli alan kaldı', 'Görüntü / Kamera', 'Lens çizik / kirli', 'normal', 'resolved', 3, [6]),
            ('USB bağlantısı test sırasında kopuyor', 'Yazılım / Bağlantı', 'USB bağlantısı kopuyor', 'normal', 'closed', 4, [2]),
            ('Askı bağlantı noktası gevşek', 'Mekanik / Aksesuar', 'Askı bağlantısı gevşek', 'low', 'new', 5, [10]),
            ('Spektral modda renk sapması raporlandı', 'Işık Kaynağı / Spektral', 'Spektral renk sapması', 'normal', 'resolved', 6, [4, 5]),
        ]

        created_tickets = []
        for index, (subject, category_name, symptom_name, priority, status, device_index, part_indexes) in enumerate(ticket_data):
            category = categories[category_name]
            symptom = symptoms[symptom_name]
            assigned = technicians[index % len(technicians)]
            created_at = timezone.now() - timedelta(days=14 - index)
            closed_at = created_at + timedelta(days=2) if status in ['resolved', 'closed'] else None

            ticket, created = ServiceTicket.objects.update_or_create(
                subject=subject,
                device=devices[device_index],
                defaults={
                    'fault_category': category,
                    'symptom': symptom,
                    'description': (
                        f'demo - Müşteri cihazda "{symptom_name}" belirtisini bildirdi. '
                        'Servis ekibi ön kontrol, bağlantı testi, görsel inceleme ve fonksiyon testlerini yapacaktır.'
                    ),
                    'root_cause': '' if status in ['new', 'investigating', 'in_progress'] else (
                        'Saha kullanımında bağlantı/aksesuar kaynaklı düzensiz temas tespit edildi.'
                    ),
                    'resolution_steps': '' if status in ['new', 'investigating'] else (
                        '1. Görsel kontrol yapıldı.\n'
                        '2. İlgili modül/parça değiştirildi veya yeniden sabitlendi.\n'
                        '3. Firmware ve fonksiyon testleri tekrarlandı.\n'
                        '4. Final doğrulama checklisti tamamlandı.'
                    ),
                    'verification_passed': True if status in ['resolved', 'closed'] else None,
                    'verification_notes': 'demo - Final testten geçti.' if status in ['resolved', 'closed'] else '',
                    'priority': priority,
                    'status': status,
                    'assigned_to': assigned,
                    'created_by': admin,
                    'closed_at': closed_at,
                },
            )
            ticket.parts_used.set([parts[i] for i in part_indexes])
            # Keep auto_now_add fields visually distributed for dashboard charts.
            ServiceTicket.objects.filter(pk=ticket.pk).update(created_at=created_at, updated_at=created_at + timedelta(hours=6), closed_at=closed_at)

            TicketComment.objects.get_or_create(
                ticket=ticket,
                author=assigned,
                body=f'demo - İlk teknik değerlendirme yapıldı. Öncelik: {ticket.get_priority_display()}.',
                defaults={'is_internal': True},
            )
            TicketComment.objects.get_or_create(
                ticket=ticket,
                author=admin,
                body='demo - Müşteri bilgilendirme notu hazırlandı ve takip planına alındı.',
                defaults={'is_internal': False},
            )
            created_tickets.append(ticket)

        article_templates = [
            ('UV LED Modülü Çalışmıyor: Hızlı Tanı ve Değişim Rehberi', 'SSFORCE', 'Işık Kaynağı / Spektral', 'UV LED yanmıyor'),
            ('HDMI Görüntü Yok Sorun Giderme Akışı', '8K', 'Yazılım / Bağlantı', 'HDMI görüntü vermiyor'),
            ('Batarya Hızlı Bitiyor: Şarj ve Hücre Sağlığı Kontrolü', '4K', 'Batarya / Güç', 'Batarya hızlı bitiyor'),
            ('T-Zoom USB Bağlantı Sorunları İçin Servis Checklisti', 'TZOOM', 'Yazılım / Bağlantı', 'USB bağlantısı kopuyor'),
            ('Darkroom Kapak Hizalama ve Mekanik Kontrol Prosedürü', 'SSFORCE', 'Mekanik / Aksesuar', 'Darkroom kapağı oturmuyor'),
            ('Macro-Micro Lens Odak Problemi İçin Temizlik ve Kalibrasyon', 'SSFORCE', 'Görüntü / Kamera', 'Odak tutmuyor'),
        ]
        for idx, (title, family, category_name, symptom_name) in enumerate(article_templates):
            category = categories[category_name]
            symptom = symptoms[symptom_name]
            article, _ = KnowledgeArticle.objects.update_or_create(
                title=title,
                defaults={
                    'summary': f'demo - {symptom_name} belirtisi için hızlı teşhis, parça kontrolü ve doğrulama akışı.',
                    'solution_body': (
                        '1. Cihaz seri no ve model bilgisini doğrula.\n'
                        '2. Görsel hasar, kablo, batarya ve aksesuar kontrolü yap.\n'
                        '3. İlgili modda fonksiyon testi çalıştır.\n'
                        '4. Gerekirse modül/parça değişimi uygula.\n'
                        '5. Final test sonucu ve müşteri bilgilendirme notunu kaydet.'
                    ),
                    'verification_checklist': (
                        '- Cihaz açılış testi geçti.\n'
                        '- İlgili spektral/görüntü modu test edildi.\n'
                        '- Bağlantı ve aksesuar kontrolleri tamamlandı.\n'
                        '- Servis kaydı güncellendi.'
                    ),
                    'device_family': family,
                    'fault_category': category,
                    'symptom': symptom,
                    'source_ticket': created_tickets[idx] if idx < len(created_tickets) else None,
                    'tags': 'demo, forenscope, servis, teknik bilgi',
                    'status': 'published' if idx < 4 else 'review',
                    'version': 1 + (idx % 2),
                    'view_count': 25 + idx * 17,
                    'author': manager,
                    'approved_by': admin if idx < 4 else None,
                    'approved_at': timezone.now() - timedelta(days=idx) if idx < 4 else None,
                },
            )

        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
        self.stdout.write(self.style.SUCCESS('Login users: admin/Admin12345!, tech.ali/Demo12345!, tech.zeynep/Demo12345!, service.manager/Demo12345!'))
        self.stdout.write(self.style.SUCCESS(f'Devices: {Device.objects.filter(serial_no__startswith="DEMO-").count()}'))
        self.stdout.write(self.style.SUCCESS(f'Tickets: {len(created_tickets)}'))
        self.stdout.write(self.style.SUCCESS(f'Articles: {KnowledgeArticle.objects.filter(tags__icontains="demo").count()}'))
