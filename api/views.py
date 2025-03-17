import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .odoo_client import search_read, create_record, update_record,delete_record
from .utils import validate_json, validate_required_params
from .models import OdooInstance
from django.core.cache import cache
from django.utils.timezone import now
from datetime import timedelta

@csrf_exempt
def get_records(request):
    """ Endpoint para consultar registros en Odoo usando autenticación con expiración de tokens """
    if request.method == "GET":
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        # 🔹 Intentamos obtener la instancia desde la caché (Redis)
        instance_data = cache.get(f"odoo_instance_{token}")

        if instance_data:
            instance_data = json.loads(instance_data)  # Convertimos de JSON a diccionario
        else:
            try:
                instance = OdooInstance.objects.get(token=token)
                if instance.is_token_expired():
                    return JsonResponse({"error": "El token ha expirado"}, status=401)
                if instance.token_lifetime == "once":
                    instance.use_once_token()

                # Guardamos la instancia en Redis como JSON
                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }
                cache.set(f"odoo_instance_{token}", json.dumps(instance_data), timeout=600)

            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)

        try:
            model = request.GET.get("model")
            domain = request.GET.get("domain", "[]")
            fields = request.GET.get("fields", "[]")

            if not model:
                return JsonResponse({"error": 'El parámetro "model" es obligatorio'}, status=400)

            domain = json.loads(domain)
            fields = json.loads(fields)

            # 🔹 Llamamos a Odoo usando la instancia correcta
            data = search_read(
                instance_data["url"],
                instance_data["database"],
                instance_data["username"],
                instance_data["password"],
                model,
                domain,
                fields
            )

            return JsonResponse({"data": data}, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


@csrf_exempt
def create_record_view(request):
    """ Endpoint para crear un registro en Odoo con validación de token """
    if request.method == "POST":
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        # 🔹 Obtener la instancia de Odoo desde Redis o la BD
        instance_data = cache.get(f"odoo_instance_{token}")

        if instance_data:
            instance_data = json.loads(instance_data)  # Convertimos de JSON a diccionario
        else:
            try:
                instance = OdooInstance.objects.get(token=token)
                if instance.is_token_expired():
                    return JsonResponse({"error": "El token ha expirado"}, status=401)
                if instance.token_lifetime == "once":
                    instance.use_once_token()

                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }
                cache.set(f"odoo_instance_{token}", json.dumps(instance_data), timeout=600)

            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)
        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            values = data.get("values", {})

            if not model or not values:
                return JsonResponse({"error": 'Faltan parámetros "model" o "values"'}, status=400)

            # 🔹 Llamar a Odoo con conexión dinámica
            record_id = create_record(
                instance_data["url"],
                instance_data["database"],
                instance_data["username"],
                instance_data["password"],
                model,
                values
            )

            return JsonResponse({"success": True, "record_id": record_id})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def update_record_view(request):
    """ Endpoint para actualizar un registro en Odoo con validación de token """
    if request.method == "PUT":
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        instance_data = cache.get(f"odoo_instance_{token}")

        if instance_data:
            instance_data = json.loads(instance_data)
        else:
            try:
                instance = OdooInstance.objects.get(token=token)
                if instance.is_token_expired():
                    return JsonResponse({"error": "El token ha expirado"}, status=401)
                if instance.token_lifetime == "once":
                    instance.use_once_token()

                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }
                cache.set(f"odoo_instance_{token}", json.dumps(instance_data), timeout=600)

            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)
        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            record_id = data.get("id")
            values = data.get("values", {})

            if not model or not record_id or not values:
                return JsonResponse({"error": 'Faltan parámetros "model", "id" o "values"'}, status=400)

            success = update_record(
                instance_data["url"],
                instance_data["database"],
                instance_data["username"],
                instance_data["password"],
                model,
                record_id,
                values
            )

            return JsonResponse({"success": success})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)

@csrf_exempt
def delete_record_view(request):
    """ Endpoint para eliminar un registro en Odoo con validación de token """
    if request.method == "DELETE":
        token = request.headers.get("Authorization")

        if not token:
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        instance_data = cache.get(f"odoo_instance_{token}")

        if instance_data:
            instance_data = json.loads(instance_data)
        else:
            try:
                instance = OdooInstance.objects.get(token=token)
                if instance.is_token_expired():
                    return JsonResponse({"error": "El token ha expirado"}, status=401)
                if instance.token_lifetime == "once":
                    instance.use_once_token()

                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }
                cache.set(f"odoo_instance_{token}", json.dumps(instance_data), timeout=600)

            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token inválido"}, status=401)

        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            record_id = data.get("id")

            if not model or not record_id:
                return JsonResponse({"error": 'Faltan parámetros "model" o "id"'}, status=400)

            success = delete_record(
                instance_data["url"],
                instance_data["database"],
                instance_data["username"],
                instance_data["password"],
                model,
                record_id
            )
            return JsonResponse({"success": success})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)


#crear tokern de autenticacion para instancia de odoo
@csrf_exempt
def register_odoo_instance(request):
    """ Endpoint para registrar una nueva instancia de Odoo con contraseña encriptada """
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

            # Crear instancia en la BD con la contraseña encriptada
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



@csrf_exempt
def revoke_token_view(request):
    """ Endpoint para revocar un token manualmente """
    if request.method == "POST":
        try:
            # 🔹 Cargar los datos de la solicitud
            data = json.loads(request.body.decode("utf-8"))
            token = data.get("token")

            print(f"🔍 Token recibido en la solicitud: {token}")  # 🛠️ Depuración

            if not token:
                return JsonResponse({"error": "Falta el parámetro 'token'"}, status=400)

            try:
                # 🔹 Buscar la instancia en la BD
                instance = OdooInstance.objects.get(token=token)
                print(f"✅ Token encontrado en BD: {instance.token}")

                # 🔹 Eliminar el token de la BD
                instance.token = None
                instance.expires_at = None
                instance.save()

                # 🔹 Eliminar el token de Redis
                cache.delete(f"odoo_instance_{token}")
                print(f"🗑️ Token eliminado de Redis: odoo_instance_{token}")

                return JsonResponse({"success": True, "message": "Token revocado correctamente"})

            except OdooInstance.DoesNotExist:
                return JsonResponse({"error": "Token no encontrado"}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Error al procesar la solicitud, formato JSON inválido"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)