from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from .models import OdooInstance
import json

class OdooInstanceMiddleware:
    """ Middleware para autenticar instancias de Odoo con tokens y caché en Redis """
    EXCLUDED_PATHS = ["/admin","/api/register_odoo_instance/", "/api/revoke_token/", "/api/verify_odoo_user/", "/api/get_asistencia_records/",
                      "/api/create_asistencia_record/","/api/update_asistencia_record/","/api/logs/"]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return self.get_response(request)

        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        instance = cache.get(f"odoo_instance_{token}")

        if not instance:
            try:
                instance = OdooInstance.objects.get(token=token)
                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }
                cache.set(f"odoo_instance_{instance.token}", json.dumps(instance_data), timeout=600)
            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)

        request.odoo_instance = instance
        return self.get_response(request)
    