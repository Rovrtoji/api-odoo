import uuid
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .odoo_client import search_read, create_record, update_record,delete_record
from .utils import validate_json, validate_required_params
from .models import OdooInstance
from django.core.cache import cache
from django.utils.timezone import now
from datetime import datetime, timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
import xmlrpc.client
import pytz
import logging
logger = logging.getLogger(__name__)


@csrf_exempt
def get_records(request):
    """ Endpoint para consultar registros en Odoo usando autenticación con logs """
    if request.method == "GET":
        token = request.headers.get("Authorization")

        if not token:
            logger.warning("❌ Falta el token en la cabecera Authorization")
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        logger.info(f"🔹 Token recibido: {token}")

        # Intentar obtener la instancia desde Redis
        instance_data = cache.get(f"odoo_instance_{token}")

        if instance_data:
            instance_data = json.loads(instance_data)
            logger.info("✅ Instancia obtenida desde Redis")
        else:
            try:
                instance = OdooInstance.objects.get(token=token)
                if instance.is_token_expired():
                    logger.warning(f"⚠ Token expirado: {token}")
                    return JsonResponse({"error": "El token ha expirado"}, status=401)

                if instance.token_lifetime == "once":
                    instance.use_once_token()
                    logger.info(f"🔄 Token de un solo uso eliminado: {token}")

                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }
                cache.set(f"odoo_instance_{token}", json.dumps(instance_data), timeout=600)
                logger.info(f"📦 Instancia {instance.name} cargada y guardada en Redis")
            except OdooInstance.DoesNotExist:
                logger.error(f"❌ Token inválido: {token}")
                return JsonResponse({"error": "Token inválido"}, status=401)

        try:
            model = request.GET.get("model")
            domain = request.GET.get("domain", "[]")
            fields = request.GET.get("fields", "[]")

            if not model:
                logger.warning("⚠ Falta el parámetro 'model'")
                return JsonResponse({"error": 'El parámetro "model" es obligatorio'}, status=400)

            domain = json.loads(domain)
            fields = json.loads(fields)

            data = search_read(
                instance_data["url"],
                instance_data["database"],
                instance_data["username"],
                instance_data["password"],
                model,
                domain,
                fields
            )

            logger.info(f"✅ Consulta realizada en Odoo para el modelo {model}")
            return JsonResponse({"data": data}, safe=False)

        except Exception as e:
            logger.error(f"❌ Error en get_records: {e}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Método no permitido"}, status=405)




@csrf_exempt
def create_record_view(request):
    """ Endpoint para crear un registro en Odoo con validación de token y logs """
    if request.method == "POST":
        token = request.headers.get("Authorization")

        if not token:
            logger.warning("❌ Falta el token en la cabecera Authorization")
            return JsonResponse({"error": "Falta el token en la cabecera Authorization"}, status=401)

        instance_data = cache.get(f"odoo_instance_{token}")

        if instance_data:
            instance_data = json.loads(instance_data)
            logger.info("✅ Instancia obtenida desde Redis")
        else:
            try:
                instance = OdooInstance.objects.get(token=token)
                if instance.is_token_expired():
                    logger.warning(f"⚠ Token expirado: {token}")
                    return JsonResponse({"error": "El token ha expirado"}, status=401)

                if instance.token_lifetime == "once":
                    instance.use_once_token()
                    logger.info(f"🔄 Token de un solo uso eliminado: {token}")

                instance_data = {
                    "url": instance.url,
                    "database": instance.database,
                    "username": instance.username,
                    "password": instance.password,
                }
                cache.set(f"odoo_instance_{token}", json.dumps(instance_data), timeout=600)
                logger.info(f"📦 Instancia {instance.name} cargada y guardada en Redis")
            except OdooInstance.DoesNotExist:
                logger.error(f"❌ Token inválido: {token}")
                return JsonResponse({"error": "Token inválido"}, status=401)

        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            values = data.get("values", {})

            if not model or not values:
                logger.warning("⚠ Faltan parámetros 'model' o 'values'")
                return JsonResponse({"error": 'Faltan parámetros "model" o "values"'}, status=400)

            record_id = create_record(
                instance_data["url"],
                instance_data["database"],
                instance_data["username"],
                instance_data["password"],
                model,
                values
            )

            logger.info(f"✅ Registro creado en Odoo (ID: {record_id}) para el modelo {model}")
            return JsonResponse({"success": True, "record_id": record_id})

        except Exception as e:
            logger.error(f"❌ Error en create_record_view: {e}")
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

"""inicia logica para asistencia"""
@api_view(["POST"])
def verify_odoo_user(request):
    """ Endpoint para verificar si un usuario y contraseña existen en Odoo y obtener su nombre """
    try:
        data = request.data
        instance_name = data.get("instance_name")
        login = data.get("login")
        password = data.get("password")

        if not all([instance_name, login, password]):
            return Response({"error": "Faltan parámetros: instance_name, login y password"}, status=400)

        # 🔹 Buscar la instancia en la BD
        try:
            instance = OdooInstance.objects.get(name=instance_name)
        except OdooInstance.DoesNotExist:
            return Response({"error": "Instancia no encontrada"}, status=404)

        # 🔹 Conectarse a Odoo y verificar credenciales
        common = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/common")
        uid = common.authenticate(instance.database, login, password, {})

        if not uid:
            return Response({"valid": False, "message": "Usuario o contraseña incorrectos"}, status=401)

        # 🔹 Si la autenticación es exitosa, obtener el nombre del usuario
        models = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/object")
        user_data = models.execute_kw(
            instance.database, uid, password,
            'res.users', 'read', [[uid]], {'fields': ['name']}
        )

        user_name = user_data[0]['name'] if user_data else "Desconocido"

        return Response({
            "valid": True,
            "message": "Usuario autenticado correctamente",
            "uid": uid,
            "name": user_name
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["GET"])
def get_asistencia_records(request):
    """ Endpoint para obtener registros de asistencia del día actual """
    try:
        data = request.query_params
        instance_name = data.get("instance_name")
        login = data.get("login")
        password = data.get("password")
        timezone = data.get("timezone", "UTC")  # Permitir definir zona horaria

        if not all([instance_name, login, password]):
            return Response({"error": "Faltan parámetros: instance_name, login y password"}, status=400)

        # 🔹 Buscar la instancia en la BD
        try:
            instance = OdooInstance.objects.get(name=instance_name)
        except OdooInstance.DoesNotExist:
            return Response({"error": "Instancia no encontrada"}, status=404)

        # 🔹 Autenticación en Odoo
        common = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/common")
        uid = common.authenticate(instance.database, login, password, {})

        if not uid:
            return Response({"valid": False, "message": "Usuario o contraseña incorrectos"}, status=401)

        # 🔹 Obtener la fecha actual con zona horaria
        tz = pytz.timezone(timezone)
        today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        today_end = datetime.now(tz).replace(hour=23, minute=59, second=59, microsecond=999999).strftime('%Y-%m-%d %H:%M:%S')

        # 🔹 Filtrar solo registros del día actual
        models = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/object")
        domain = [['horaIngreso', '>=', today_start], ['horaIngreso', '<', today_end]]
        records = models.execute_kw(
            instance.database, uid, password,
            'asi.asistencia', 'search_read', [domain],
            {'fields': ['name', 'empleadoId', 'horaIngreso','horaSalidaComida', 'horaSalida','horaRegresoComida','id']}
        )

        return Response({"data": records})

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
def create_asistencia_record(request):
    """ Endpoint para crear un registro de asistencia """
    try:
        data = request.data
        instance_name = data.get("instance_name")
        login = data.get("login")
        password = data.get("password")
        values = data.get("values", {})

        if not all([instance_name, login, password, values]):
            return Response({"error": "Faltan parámetros: instance_name, login, password y values"}, status=400)

        # 🔹 Buscar la instancia en la BD
        try:
            instance = OdooInstance.objects.get(name=instance_name)
        except OdooInstance.DoesNotExist:
            return Response({"error": "Instancia no encontrada"}, status=404)

        # 🔹 Autenticación en Odoo
        common = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/common")
        uid = common.authenticate(instance.database, login, password, {})

        if not uid:
            return Response({"valid": False, "message": "Usuario o contraseña incorrectos"}, status=401)

        # 🔹 Crear registro en Odoo
        models = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/object")
        record_id = models.execute_kw(
            instance.database, uid, password,
            'asi.asistencia', 'create', [values]
        )

        return Response({"success": True, "record_id": record_id})

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["PUT"])
def update_asistencia_record(request):
    """ Endpoint para actualizar un registro de asistencia SOLO del día actual """
    try:
        data = request.data
        instance_name = data.get("instance_name")
        login = data.get("login")
        password = data.get("password")
        record_id = data.get("id")
        values = data.get("values", {})
        timezone = data.get("timezone", "UTC")

        if not all([instance_name, login, password, record_id, values]):
            return Response({"error": "Faltan parámetros: instance_name, login, password, id y values"}, status=400)

        # 🔹 Buscar la instancia en la BD
        try:
            instance = OdooInstance.objects.get(name=instance_name)
        except OdooInstance.DoesNotExist:
            return Response({"error": "Instancia no encontrada"}, status=404)

        # 🔹 Autenticación en Odoo
        common = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/common")
        uid = common.authenticate(instance.database, login, password, {})

        if not uid:
            return Response({"valid": False, "message": "Usuario o contraseña incorrectos"}, status=401)

        # 🔹 Obtener la fecha actual
        tz = pytz.timezone(timezone)
        today_start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        today_end = datetime.now(tz).replace(hour=23, minute=59, second=59, microsecond=999999).strftime('%Y-%m-%d %H:%M:%S')

        # 🔹 Verificar si el registro pertenece al día actual
        models = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/object")
        record = models.execute_kw(
            instance.database, uid, password,
            'asi.asistencia', 'read', [[record_id]], {'fields': ['horaIngreso']}
        )

        if not record or not (today_start <= record[0]['horaIngreso'] <= today_end):
            return Response({"error": "Solo se pueden actualizar registros del día actual"}, status=403)

        # 🔹 Actualizar el registro
        success = models.execute_kw(
            instance.database, uid, password,
            'asi.asistencia', 'write', [[record_id], values]
        )

        return Response({"success": success})

    except Exception as e:
        return Response({"error": str(e)}, status=500)
