"""Excepción de negocio (Arquitectura 7.7)."""


class ErrorNegocio(Exception):
    """Error esperado de una regla de negocio. Su mensaje se muestra al usuario."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje
