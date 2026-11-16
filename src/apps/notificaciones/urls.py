from django.urls import path

from . import views

app_name = "notificaciones"

urlpatterns = [
    path("", views.vencidos, name="vencidos"),
    path("<int:pago_id>/enviar/", views.enviar_correo, name="enviar"),
    path("<int:pago_id>/correos/", views.correos_del_vencimiento, name="correos"),
    path("<int:pago_id>/contacto/", views.registrar_contacto, name="contacto"),
    path("correo/<int:aviso_id>/", views.ver_correo, name="correo"),
]
