from django.core.cache import cache
from django.http import JsonResponse
from .models import OdooInstance
import json

class OdooInstanceMiddleware:
    """ Middleware para autenticar instancias de Odoo con tokens y caché en Redis """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        # 🔹 Intentamos obtener la instancia desde la caché de Redis
        instance = cache.get(f"odoo_instance_{token}")

        if not instance:
            try:
                instance = OdooInstance.objects.get(token=token)
                # 🔹 Guardamos la instancia en Redis para acelerar futuras solicitudes

                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }

                cache.set(f"odoo_instance_{instance.token}", json.dumps(instance_data),
                          timeout=600)  # Cache por 10 minutos
            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)

        request.odoo_instance = instance  # Asignamos la instancia al request
        return self.get_response(request)
