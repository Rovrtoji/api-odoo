from django.core.management.base import BaseCommand
from api.models import OdooInstance

class Command(BaseCommand):
    help = 'Renueva tokens de instancias Odoo con lifetime="once" cada 24 horas'

    def handle(self, *args, **kwargs):
        instances = OdooInstance.objects.filter(token_lifetime="once")
        if not instances.exists():
            self.stdout.write(self.style.WARNING('No hay instancias con token tipo "once"'))
            return

        for instance in instances:
            instance.generate_token("once")
            self.stdout.write(self.style.SUCCESS(
                f"✅ Token actualizado para: {instance.name}, expira: {instance.expires_at}"
            ))
