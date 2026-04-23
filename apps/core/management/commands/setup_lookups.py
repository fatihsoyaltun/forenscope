from django.core.management.base import BaseCommand
from apps.service.models import FaultCategory, Symptom, Part


CATEGORIES_AND_SYMPTOMS = {
    'Mekanik': [
        'Filtre takılıyor',
        'Motor dönmüyor',
        'Lens hareketsiz',
        'Mekanik titreşim',
        'Kapak açılmıyor',
    ],
    'Optik': [
        'Light system error',
        'Görüntü yok',
        'Renk hatası',
        'Odak kaybı',
        'Lens kirliliği',
    ],
    'Yazılım': [
        'Sistem açılmıyor',
        'Yazılım donma',
        'Bağlantı kopuyor',
        'Güncelleme hatası',
        'Konfigürasyon kaybı',
    ],
    'Güç': [
        'Cihaz açılmıyor',
        'Kısa devre',
        'Şarj olmuyor',
        'Güç dalgalanması',
        'Anakart arızası',
    ],
    'Bağlantı': [
        'HDMI sinyali yok',
        'USB algılanmıyor',
        'Wi-Fi bağlanmıyor',
        'Ethernet kopuyor',
        'SDI çıkışı yok',
    ],
    'Kalibrasyon': [
        'Kalibrasyon hatası',
        'Sıcaklık sapması',
        'Renk kalibrasyonu bozuk',
        'Lens kalibrasyonu gerekli',
    ],
}

PARTS = [
    ('PCB-MOTOR-V2', 'PCB Motor Board v2'),
    ('FILTER-8K-REV3', 'Filtre Mekanizması 8K Rev3'),
    ('FILTER-4K-REV2', 'Filtre Mekanizması 4K Rev2'),
    ('HDMI-BOARD-V1', 'HDMI Çıkış Kartı v1'),
    ('LENS-ASSY-4K', 'Lens Assembly 4K'),
    ('LENS-ASSY-8K', 'Lens Assembly 8K'),
    ('PSU-12V-3A', 'Güç Kaynağı 12V 3A'),
    ('MAIN-PCB-8K', 'Ana Kart 8K'),
    ('MAIN-PCB-4K', 'Ana Kart 4K'),
    ('FAN-60MM', 'Soğutma Fanı 60mm'),
    ('CABLE-HDMI-30CM', 'HDMI Kablo 30cm'),
    ('MOTOR-DRV-V3', 'Motor Sürücü v3'),
]


class Command(BaseCommand):
    help = 'Seed fault categories, symptoms and parts'

    def handle(self, *args, **options):
        for cat_name, symptoms in CATEGORIES_AND_SYMPTOMS.items():
            cat, created = FaultCategory.objects.get_or_create(name=cat_name)
            status = 'created' if created else 'exists'
            self.stdout.write(f'  Category "{cat_name}": {status}')
            for sym_name in symptoms:
                Symptom.objects.get_or_create(category=cat, name=sym_name)
            self.stdout.write(f'    {len(symptoms)} symptoms: OK')

        for code, name in PARTS:
            Part.objects.get_or_create(code=code, defaults={'name': name})
        self.stdout.write(self.style.SUCCESS(f'\n{len(PARTS)} parts: OK'))

        self.stdout.write(self.style.SUCCESS('\nLookup data seeded successfully.'))
