from django.shortcuts import render
from django.http import HttpResponse
import os

LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "api_logs.log")


def logs_view(request):
    """ Vista web para ver los logs en tiempo real con auto-refresh """
    try:
        with open(LOG_FILE_PATH, "r") as log_file:
            logs = log_file.readlines()

        log_content = "".join(logs[-50:])  # Últimos 50 registros

        html = f"""
        <html>
        <head>
            <meta http-equiv="refresh" content="5"> <!-- Auto-refresh cada 5 segundos -->
            <title>Logs de la API</title>
        </head>
        <body>
            <h2>Logs de la API (últimos 50 registros)</h2>
            <pre>{log_content}</pre>
        </body>
        </html>
        """
        return HttpResponse(html)
    except Exception as e:
        return HttpResponse(f"Error al leer los logs: {e}")
