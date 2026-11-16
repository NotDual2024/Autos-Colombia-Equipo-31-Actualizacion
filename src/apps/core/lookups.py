"""Lookups personalizados para reproducir en Django las restricciones GLOB
del modelo físico aprobado (docs/sql/ddl_sqlite_v1.sql)."""
from django.db.models import CharField, Lookup, TextField
from django.db.models.functions import Length, Trim


@CharField.register_lookup
class Glob(Lookup):
    """campo__glob='[A-Z]*'  ->  campo GLOB '[A-Z]*'  (SQLite, sensible a mayúsculas)."""

    lookup_name = "glob"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        return f"{lhs} GLOB {rhs}", [*lhs_params, *rhs_params]


CharField.register_lookup(Length)
# Texto no vacío: campo__trim__length__gt=0  ->  length(trim(campo)) > 0
TextField.register_lookup(Trim)
TextField.register_lookup(Length)
