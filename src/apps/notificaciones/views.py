"""Vencidos, correos simulados y contacto con autoridades (HU-007 a HU-009, HU-011; M-08 a M-11)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.errores import ErrorNegocio
from apps.cuentas.permisos import solo_administrador

from . import services
from .models import AvisoCorreo


@login_required
def vencidos(request):
    """HU-007 / UC-10 (y puntos de extensión de UC-12 y UC-14)."""
    return render(request, "notificaciones/vencidos.html", {"filas": services.vencidos_dentro(), "plazo": services.PLAZO_DIAS})


@login_required
@require_POST
def enviar_correo(request, pago_id: int):
    """HU-011 / UC-12. Si ya hubo un envío, pide confirmación (RN-22)."""
    confirmar = request.POST.get("confirmar") == "1"
    try:
        aviso = services.enviar_manual(pago_id, request.user, confirmar_reenvio=confirmar)
    except services.RequiereConfirmacion as pregunta:
        fila = services.vencimiento_de_pago(pago_id)
        return render(request, "notificaciones/confirmar_reenvio.html", {"fila": fila, "pregunta": pregunta.mensaje})
    except ErrorNegocio as error:
        messages.error(request, error.mensaje)
        return redirect("notificaciones:vencidos")
    if aviso.resultado == "FALLIDO":
        messages.error(request, "El envío falló y quedó registrado. Puedes intentarlo de nuevo.")
        return redirect("notificaciones:vencidos")
    return redirect("notificaciones:correo", aviso_id=aviso.pk)


@login_required
def ver_correo(request, aviso_id: int):
    """M-10: contenido del correo simulado (HU-008, HU-011)."""
    aviso = get_object_or_404(AvisoCorreo.objects.select_related("pago__vehiculo__propietario", "enviado_por"), pk=aviso_id)
    return render(request, "notificaciones/correo.html", {"aviso": aviso})


@login_required
def correos_del_vencimiento(request, pago_id: int):
    avisos = AvisoCorreo.objects.filter(pago_id=pago_id).select_related("pago__vehiculo", "enviado_por").order_by("fecha_hora")
    if not avisos:
        messages.warning(request, "Todavía no hay correos para este vencimiento.")
        return redirect("notificaciones:vencidos")
    return render(request, "notificaciones/correos.html", {"avisos": avisos, "vehiculo": avisos[0].pago.vehiculo})


@solo_administrador
@require_http_methods(["GET", "POST"])
def registrar_contacto(request, pago_id: int):
    """HU-009 / UC-14: solo administrador (los operadores reciben 403, acceso denegado)."""
    try:
        fila = services.vencimiento_de_pago(pago_id)
    except ErrorNegocio as error:
        messages.error(request, error.mensaje)
        return redirect("notificaciones:vencidos")
    error = None
    if request.method == "POST":
        try:
            services.registrar_contacto(pago_id, request.user, request.POST.get("observacion", ""))
            messages.success(request, f"Contacto con autoridades registrado para {fila.vehiculo.placa}.")
            return redirect("notificaciones:vencidos")
        except ErrorNegocio as e:
            error = e.mensaje
    return render(request, "notificaciones/contacto.html", {
        "fila": fila, "error": error, "contactos": fila.pago.contactos_autoridad.select_related("registrado_por"),
        "observacion": request.POST.get("observacion", ""),
    })
