from django.db import models
import uuid

class OdooInstance(models.Model):
    """ Modelo para almacenar las credenciales de cada instancia de Odoo """
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField()
    database = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True, blank=True, null=True)

    def generate_token(self):
        """ Genera un token único para la instancia """
        self.token = str(uuid.uuid4())
        self.save()

    def __str__(self):
        return self.name
