from django.db import models
import uuid
from django.contrib.auth.hashers import make_password, check_password
from datetime import timedelta, datetime, timezone
from django.utils.timezone import now


class OdooInstance(models.Model):
    name = models.CharField(max_length=255, unique=True)
    url = models.URLField()
    database = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)  # 🔒 Guardado encriptado
    token = models.CharField(max_length=255, null=True, blank=True, unique=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    token_lifetime = models.CharField(
        max_length=10,
        choices=[("once", "Una vez"), ("30d", "30 días"), ("60d", "60 días"), ("forever", "Para siempre")],
        default="30d"
    )

    def generate_token(self, lifetime=None):
        """ Genera un nuevo token con la expiración correcta """
        self.token = str(uuid.uuid4())

        if lifetime is None:
            lifetime = self.token_lifetime

        if lifetime == "forever":
            self.expires_at = None
        else:
            days = int(lifetime.replace("d", ""))
            self.expires_at = now() + timedelta(days=days)

        self.save()

    def save(self, *args, **kwargs):
        # """Sobreescribir el método save() para encriptar la contraseña antes de guardar."""
        # if not self.password.startswith("pbkdf2_sha256$"):
        #     self.password = make_password(self.password)  # 🔒 Encriptar la contraseña
        super(OdooInstance, self).save(*args, **kwargs)

    def check_password(self, raw_password):
        """Verifica si la contraseña ingresada coincide con la almacenada encriptada."""
        return check_password(raw_password, self.password)

    def generate_token(self, lifetime="30d"):
        """Genera un token único para la instancia de Odoo"""
        self.token = str(uuid.uuid4())
        self.expires_at = None if lifetime == "forever" else timezone.now() + timedelta(
            days=int(lifetime.replace("d", "")))
        self.save()

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
