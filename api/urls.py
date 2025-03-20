from django.urls import path
from .views import get_records, create_record_view, update_record_view, delete_record_view, register_odoo_instance, verify_odoo_user,revoke_token_view
from .views import get_asistencia_records, create_asistencia_record, update_asistencia_record
urlpatterns = [
    path('get_records/', get_records, name='get_records'),
    path('create_record/', create_record_view, name='create_record'),
    path('update_record/', update_record_view, name='update_record'),
    path('delete_record/', delete_record_view, name='delete_record'),
    path('register_odoo_instance/', register_odoo_instance, name='register_odoo_instance'),
    path("revoke_token/", revoke_token_view, name="revoke_token"),
    path("verify_odoo_user/", verify_odoo_user, name="verify_odoo_user"),
    path("get_asistencia_records/", get_asistencia_records, name="get_asistencia_records"),
    path("create_asistencia_record/", create_asistencia_record, name="create_asistencia_record"),
    path("update_asistencia_record/", update_asistencia_record, name="update_asistencia_record"),
]
