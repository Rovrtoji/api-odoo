import xmlrpc.client
from api.models import OdooInstance

def authenticate(odoo_url, db, username, password):
    """Autenticarse en Odoo y obtener el UID dinámico."""
    common = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise Exception("Error de autenticación en Odoo")
    return uid


def search_read(odoo_url, db, username, password, model, domain=[], fields=[]):
    """Consulta registros en Odoo con conexión dinámica."""
    uid = authenticate(odoo_url, db, username, password)
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

    return models.execute_kw(
        db, uid, password, model, 'search_read',
        [domain], {'fields': fields}
    )


def create_record(odoo_url, db, username, password, model, values):
    """Crea un registro en Odoo con conexión dinámica."""
    uid = authenticate(odoo_url, db, username, password)
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

    return models.execute_kw(
        db, uid, password, model, 'create', [values]
    )


def update_record(odoo_url, db, username, password, model, record_id, values):
    """Actualiza un registro en Odoo con conexión dinámica."""
    uid = authenticate(odoo_url, db, username, password)
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

    return models.execute_kw(
        db, uid, password, model, 'write', [[record_id], values]
    )


def delete_record(odoo_url, db, username, password, model, record_id):
    """Elimina un registro en Odoo con conexión dinámica."""
    uid = authenticate(odoo_url, db, username, password)
    models = xmlrpc.client.ServerProxy(f'{odoo_url}/xmlrpc/2/object')

    return models.execute_kw(
        db, uid, password, model, 'unlink', [[record_id]]
    )

def connect_to_odoo(instance_name):
    """Establece conexión con Odoo usando la instancia almacenada"""
    try:
        instance = OdooInstance.objects.get(name=instance_name)

        # 🔹 Verificar la contraseña con `check_password()`
        if not instance.check_password("admin"):  # Aquí debes pasar la contraseña real
            return {"error": "Contraseña incorrecta"}

        common = xmlrpc.client.ServerProxy(f"{instance.url}/xmlrpc/2/common")
        uid = common.authenticate(instance.database, instance.username, "admin", {})

        if not uid:
            return {"error": "Error de autenticación en Odoo"}

        return {"uid": uid, "instance": instance}

    except OdooInstance.DoesNotExist:
        return {"error": "Instancia no encontrada"}