from django.shortcuts import render
from django.http import HttpResponse
import os

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api_logs.log")


def logs_view(request):
    """ Vista para ver logs con auto-limpieza si el archivo es demasiado grande """
    try:
        if os.path.exists(LOG_FILE_PATH):
            file_size = os.path.getsize(LOG_FILE_PATH) / (1024 * 1024)  # Convertir a MB

            if file_size > 10:  # Si el archivo es mayor a 10 MB, lo borra
                with open(LOG_FILE_PATH, "w") as log_file:
                    log_file.write("")

        with open(LOG_FILE_PATH, "r") as log_file:
            logs = log_file.readlines()

        html = f"""
        <html>
        <head>
            <meta http-equiv="refresh" content="5">
            <title>Logs de la API</title>
        </head>
        <body>
            <h2>Logs de la API (últimos 50 registros)</h2>
            <pre>{''.join(logs[-50:])}</pre>
        </body>
        </html>
        """
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"Error al leer los logs: {e}")
