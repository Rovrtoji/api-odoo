from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .odoo_client import search_read, create_record, update_record
from .utils import validate_json, validate_required_params


def get_records(request):
    """
    Endpoint para consultar registros en Odoo usando `search_read`.
    Requiere parámetros:
    - model: nombre del modelo en Odoo
    - domain: lista JSON con condiciones (opcional, por defecto [])
    - fields: lista JSON con los campos a recuperar (opcional, por defecto [])
    """
    model = request.GET.get('model')
    domain = request.GET.get('domain', '[]')  # Si no hay domain, por defecto es []
    fields = request.GET.get('fields', '[]')  # Si no hay fields, por defecto es []

    try:
        domain = eval(domain)  # Convertir string JSON a lista Python
        fields = eval(fields)

        if not model:
            return JsonResponse({'error': 'El parámetro "model" es obligatorio'}, status=400)

        data = search_read(model, domain, fields)
        return JsonResponse({'data': data}, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
@csrf_exempt
def create_record_view(request):
    """ Endpoint para crear un registro en Odoo con validaciones mejoradas """
    if request.method == "POST":
        data = validate_json(request)
        if isinstance(data, JsonResponse):
            return data

        missing_params = validate_required_params(data, ["model", "values"])
        if missing_params:
            return missing_params

        model, values = data["model"], data["values"]
        record_id = create_record(model, values)

        if record_id:
            return JsonResponse({'success': True, 'record_id': record_id})
        return JsonResponse({'error': 'No se pudo crear el registro.'}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)

@csrf_exempt
def update_record_view(request):
    """ Endpoint para actualizar un registro en Odoo """
    if request.method == "PUT":
        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            record_id = data.get("id")
            values = data.get("values", {})

            if not model or not record_id or not values:
                return JsonResponse({'error': 'Faltan parámetros "model", "id" o "values"'}, status=400)

            success = update_record(model, record_id, values)
            return JsonResponse({'success': success})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
@csrf_exempt
def delete_record_view(request):
    """ Endpoint para eliminar un registro en Odoo """
    if request.method == "DELETE":
        try:
            data = json.loads(request.body.decode("utf-8"))
            model = data.get("model")
            record_id = data.get("id")

            if not model or not record_id:
                return JsonResponse({'error': 'Faltan parámetros "model" o "id"'}, status=400)

            from .odoo_client import delete_record  # Importación aquí para evitar errores circulares
            success = delete_record(model, record_id)

            if success:
                return JsonResponse({'success': True, 'message': f'Registro {record_id} eliminado con éxito.'})
            else:
                return JsonResponse({'error': f'No se pudo eliminar el registro {record_id}.'}, status=500)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método no permitido'}, status=405)
