from django.db import models
import uuid
from  datetime import timedelta, datetime

class OdooInstance(models.Model):
    #Modelo para almacenar credenciales y tokens de instancias de odoo
    EXPIRATION_CHOICES = [
        ("once", "Una vez"),
        ("30d", "30 días"),
        ("60d", "60 días"),
        ("forever", "Para Siempre"),
    ]
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField()
    database = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    token = models.CharField(max_length=255, unique=True, blank=True, null=True)
    token_lifetime = models.CharField(max_length=10, choices=EXPIRATION_CHOICES, default="forever")
    expires_at = models.DateTimeField(null=True, blank=True)


    def generate_token(self, lifetime="forever"):
        """ Genera un token único para la instancia """
        self.token = str(uuid.uuid4())
        self.token_lifetime = lifetime

        if lifetime =="30d":
            self.expires_at = datetime.now() + timedelta(days=30)
        elif lifetime =="60d":
            self.expires_at = datetime.now() + timedelta(days=60)
        elif lifetime =="once":
            self.expires_at = datetime.now() + timedelta(minutes=10)
        else:
            self.expires_at = None

        self.save()

    def is_token_expierd(self):
        """vefifica que el token no este expirado"""
        if self.token_lifetime == "forever":
            return False #nunca expira
        if self.expires_at and datetime.now() > self.expires_at:
            return True
        return False

    def use_once_token(self):
        """Verifica si el token es de uso único y lo elimina"""
        if self.token_lifetime == "once":
            self.token = None
            self.expires_at = None
            self.save()

    def __str__(self):
        return f"{self.name} - {self.token_lifetime}"
