import xmlrpc.client


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
