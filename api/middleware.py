from django.http import JsonResponse
from .models import OdooInstance


class OdooInstanceMiddleware:
    """ Middleware para autenticar instancias de Odoo con tokens """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        try:
            instance = OdooInstance.objects.get(token=token)
            request.odoo_instance = instance  # Guardamos la instancia en el request
        except OdooInstance.DoesNotExist:
            return JsonResponse({"error": "Token inválido"}, status=401)

        return self.get_response(request)
