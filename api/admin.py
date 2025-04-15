from django.contrib import admin, messages
from .models import OdooInstance

@admin.register(OdooInstance)
class OdooInstanceAdmin(admin.ModelAdmin):
    readonly_fields = ('token', 'expires_at')
    list_display = ('name', 'url', 'token_lifetime', 'token', 'expires_at')
    actions = ['renew_token_now']

    def save_model(self, request, obj: OdooInstance, form, change):
        if not obj.token:
            obj.generate_token(obj.token_lifetime)
        super().save_model(request, obj, form, change)

    def renew_token_now(self, request, queryset):
        for instance in queryset:
            instance.generate_token(instance.token_lifetime)
            self.message_user(
                request,
                f"✅ Token renovado para: {instance.name}",
                messages.SUCCESS
            )
    renew_token_now.short_description = "🔁 Renovar token ahora"
