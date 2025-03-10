from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .odoo_client import search_read, create_record, update_record,delete_record
from .utils import validate_json, validate_required_params
from .models import OdooInstance
from django.core.cache import cache

def get_records(request):
    """
    Endpoint para consultar registros en Odoo usando `search_read`.
    Requiere parámetros:
    - model: nombre del modelo en Odoo
    - domain: lista JSON con condiciones (opcional, por defecto [])
    - fields: lista JSON con los campos a recuperar (opcional, por defecto [])
    """
    if request.method == 'GET':
        try:
            # obtener token de la cabecera
            token = request.headers.get("Authorization")
            if not token:
                return JsonResponse({'error': 'No token provided.'}, status=401)

            instance = cache.get(f"odoo_instance_{token}")
            if not instance:
                try:
                    instance = OdooInstance.objects.get(token=token)
                    #guardamos la instancia en Redis para acelerar futuras solicitudes
                    cache.set(f"odoo_instance_{token}", instance, timeout=600)  # Cache por 10 minutos
                except OdooInstance.DoesNotExist:
                    return JsonResponse({"error": "Token inválido"}, status=401)
            model = request.GET.get('model')
            domain = request.GET.get('domain', '[]')  # Si no hay domain, por defecto es []
            fields = request.GET.get('fields', '[]')  # Si no hay fields, por defecto es []

            if not model:
                return JsonResponse({'error': 'El parámetro "model" es obligatorio'}, status=400)

            #convertimos los parametrros JSON a lista python
            domain = json.loads(domain)
            fields = json.loads(fields)
            data = search_read(instance.url, instance.database, instance.username, instance.password, model, domain, fields)
            return JsonResponse({"data": data}, safe=False)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
def create_record_view(request):
    """ Endpoint para crear un registro en Odoo usando autenticación dinámica """
    if request.method == "POST":
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        # 🔹 Obtener la instancia desde Redis o la BD
        instance = cache.get(f"odoo_instance_{token}")

        if not instance:
            try:
                instance = OdooInstance.objects.get(token=token)
                cache.set(f"odoo_instance_{token}", instance, timeout=600)
            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)

        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            values = data.get("values", {})

            if not model or not values:
                return JsonResponse({"error": 'Faltan parámetros "model" o "values"'}, status=400)

            # 🔹 Llamar a Odoo con conexión dinámica
            record_id = create_record(instance.url, instance.database, instance.username, instance.password, model, values)

            return JsonResponse({"success": True, "record_id": record_id})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def update_record_view(request):
    """ Endpoint para actualizar un registro en Odoo usando autenticación dinámica """
    if request.method == "PUT":
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        # 🔹 Obtener la instancia desde Redis o la BD
        instance = cache.get(f"odoo_instance_{token}")

        if not instance:
            try:
                instance = OdooInstance.objects.get(token=token)
                cache.set(f"odoo_instance_{token}", instance, timeout=600)
            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)

        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            record_id = data.get("id")
            values = data.get("values", {})

            if not model or not record_id or not values:
                return JsonResponse({"error": 'Faltan parámetros "model", "id" o "values"'}, status=400)

            # 🔹 Llamar a Odoo con conexión dinámica
            success = update_record(instance.url, instance.database, instance.username, instance.password, model, record_id, values)

            return JsonResponse({"success": success})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)
@csrf_exempt
def delete_record_view(request):
    """ Endpoint para eliminar un registro en Odoo usando autenticación dinámica """
    if request.method == "DELETE":
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        # 🔹 Obtener la instancia desde Redis o la BD
        instance = cache.get(f"odoo_instance_{token}")

        if not instance:
            try:
                instance = OdooInstance.objects.get(token=token)
                cache.set(f"odoo_instance_{token}", instance, timeout=600)
            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)

        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            record_id = data.get("id")

            if not model or not record_id:
                return JsonResponse({"error": 'Faltan parámetros "model" o "id"'}, status=400)

            # 🔹 Llamar a Odoo con conexión dinámica
            success = delete_record(instance.url, instance.database, instance.username, instance.password, model, record_id)

            return JsonResponse({"success": success})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


#crear tokern de autenticacion para instancia de odoo
@csrf_exempt
def register_odoo_instance(request):
    """ Endpoint para registrar una nueva instancia de Odoo """
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get("name")
            url = data.get("url")
            database = data.get("database")
            username = data.get("username")
            password = data.get("password")

            if not all([name, url, database, username, password]):
                return JsonResponse({"error": "Faltan parámetros"}, status=400)

            instance, created = OdooInstance.objects.get_or_create(
                name=name,
                defaults={"url": url, "database": database, "username": username, "password": password}
            )

            if not created:
                return JsonResponse({"error": "La instancia ya existe"}, status=400)

            instance.generate_token()  # Generar token automáticamente
            return JsonResponse({"success": True, "token": instance.token})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)