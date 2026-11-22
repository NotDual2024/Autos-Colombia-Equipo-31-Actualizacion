"""Ayuda para las migraciones que amplían las acciones y entidades de la bitácora."""
from django.db import migrations, models



def operaciones(acciones_extra, entidades_extra):
    import importlib

    base = importlib.import_module("apps.bitacora.migrations.0002_acciones_iteracion3")
    acciones = base.ACCIONES + acciones_extra
    entidades = base.ENTIDADES + entidades_extra
    return [
        migrations.RemoveConstraint(model_name="registrooperacion", name="ck_bitacora_accion"),
        migrations.RemoveConstraint(model_name="registrooperacion", name="ck_bitacora_entidad"),
        migrations.AlterField(model_name="registrooperacion", name="accion",
                              field=models.CharField(choices=acciones, max_length=25)),
        migrations.AlterField(model_name="registrooperacion", name="entidad",
                              field=models.CharField(choices=entidades, max_length=20)),
        migrations.AddConstraint(model_name="registrooperacion", constraint=models.CheckConstraint(
            condition=models.Q(accion__in=[a for a, _ in acciones]), name="ck_bitacora_accion")),
        migrations.AddConstraint(model_name="registrooperacion", constraint=models.CheckConstraint(
            condition=models.Q(entidad__in=[e for e, _ in entidades]), name="ck_bitacora_entidad")),
    ]
