from django.core.management.base import BaseCommand
from main.models import Zone
from django.utils import timezone

class Command(BaseCommand):
    help = 'Обновляет доступность всех зон'
    
    def handle(self, *args, **options):
        zones = Zone.objects.all()
        updated_count = 0
        
        for zone in zones:
            old_seats = zone.available_seats
            zone.update_availability()
            
            if old_seats != zone.available_seats:
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Зона "{zone.title}" обновлена: {old_seats} -> {zone.available_seats}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Обновлено {updated_count} из {zones.count()} зон')
        )