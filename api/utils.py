import json
from django.http import JsonResponse

def validate_json(request):
    """ Valida si el request contiene un JSON válido """
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato JSON inválido'}, status=400)

def validate_required_params(data, required_fields):
    """ Verifica si existen los campos obligatorios en el request """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return JsonResponse({'error': f'Faltan parámetros: {", ".join(missing_fields)}'}, status=400)
    return None
