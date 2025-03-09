import xmlrpc.client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'internas')
ODOO_USER = os.getenv('ODOO_USER', 'ricardo')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'Comsys')

# Conectar con el servicio XML-RPC
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

if uid:
    print(f'Conectado a Odoo con UID: {uid}')
else:
    print('Error de autenticación en Odoo')

# Conectar con los modelos
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

def search_read(model, domain, fields):
    """Consulta registros en Odoo."""
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, 'search_read', [domain], {'fields': fields})

def create_record(model, values):
    """Crea un registro en Odoo."""
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, 'create', [values])

def update_record(model, record_id, values):
    """Actualiza un registro en Odoo."""
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, 'write', [[record_id], values])

def delete_record(model, record_id):
    """Elimina un registro en Odoo."""
    return models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, model, 'unlink', [[record_id]])

