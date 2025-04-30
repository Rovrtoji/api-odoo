from django.contrib import admin
from .models import OdooInstance

@admin.register(OdooInstance)
class OdooInstanceAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "token", "token_lifetime", "expires_at")
    readonly_fields = ("token", "expires_at")
    actions = ["generar_token"]

    @admin.action(description="🎟 Generar token de acceso")
    def generar_token(self, request, queryset):
        for instance in queryset:
            instance.generate_token(instance.token_lifetime)
        self.message_user(request, "🔑 Token generado exitosamente.")
