import sqlite3
import sys

ddl = open(sys.argv[1], encoding="utf-8").read()
db = sqlite3.connect(":memory:")
db.executescript(ddl)
db.execute("PRAGMA foreign_keys = ON")
print("SQLite", sqlite3.sqlite_version, "- tablas:",
      [r[0] for r in db.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%'")])

ok = fail = 0


def debe(desc, sql, params=(), falla=False):
    global ok, fail
    try:
        db.execute(sql, params)
        exito = not falla
    except sqlite3.IntegrityError as e:
        exito = falla
        desc += f"  [{e}]"
    print(("PASA " if exito else "FALLA") + " - " + desc)
    ok += exito
    fail += not exito


d = "2026-11-15 08:00:00"
debe("crear admin", "insert into cuentas_usuario values (1,'admin','h','A','B','ADMINISTRADOR',1,?,null)", (d,))
debe("rol inválido rechazado", "insert into cuentas_usuario values (2,'x','h','A','B','JEFE',1,?,null)", (d,), True)
debe("propietario", "insert into usuarios_celdas_propietario values (1,'Ana Gil','1023456789','3001234567','a@b.co','Cra 1 # 2-3',1,?)", (d,))
debe("cédula duplicada rechazada", "insert into usuarios_celdas_propietario values (2,'X Y','1023456789','3001112233','x@y.co','Calle 9',1,?)", (d,), True)
debe("P-23: cédula con letras rechazada", "insert into usuarios_celdas_propietario values (3,'X Y','10A3456','3001112233','x@y.co','Calle 9',1,?)", (d,), True)
debe("vehículo carro", "insert into usuarios_celdas_vehiculo values (1,'ABC123','CARRO','Chevrolet','Spark',2020,'Rojo',1,1,?)", (d,))
debe("vehículo moto", "insert into usuarios_celdas_vehiculo values (2,'XYZ12D','MOTO','Yamaha','NMAX',2023,'Negro',1,1,?)", (d,))
debe("tipo de vehículo inválido rechazado", "insert into usuarios_celdas_vehiculo values (3,'QQQ111','BUS','M','N',2020,'Azul',1,1,?)", (d,), True)
debe("propietario inexistente rechazado (FK)", "insert into usuarios_celdas_vehiculo values (4,'QQQ222','CARRO','M','N',2020,'Azul',99,1,?)", (d,), True)
debe("celda C-001", "insert into usuarios_celdas_celda values (1,'C-001','CARRO_CAMIONETA',1)")
debe("celda C-002", "insert into usuarios_celdas_celda values (2,'C-002','CARRO_CAMIONETA',1)")
debe("tarifa carro", "insert into pagos_tarifa values (1,'CARRO_CAMIONETA',150000,'2026-01-01')")
debe("tarifa con valor 0 rechazada", "insert into pagos_tarifa values (2,'MOTO',0,'2026-01-01')", (), True)
debe("pago", "insert into pagos_pago values (1,1,'2026-10-16','2026-11-15',150000,?,1)", (d,))
debe("pago con periodo invertido rechazado", "insert into pagos_pago values (2,1,'2026-11-15','2026-10-16',150000,?,1)", (d,), True)
debe("entrada del carro en C-001", "insert into entradas_salidas_estadia values (1,1,1,?,1,null,null)", (d,))
debe("RN-04: segunda estadía abierta del mismo vehículo rechazada", "insert into entradas_salidas_estadia values (2,1,2,?,1,null,null)", (d,), True)
debe("RN-05: otra estadía abierta en la celda ocupada rechazada", "insert into entradas_salidas_estadia values (3,2,1,?,1,null,null)", (d,), True)
debe("salida sin usuario de salida rechazada", "update entradas_salidas_estadia set fecha_hora_salida='2026-11-15 09:00:00' where id=1", (), True)
debe("salida anterior a la entrada rechazada", "update entradas_salidas_estadia set fecha_hora_salida='2026-11-15 07:00:00', usuario_salida_id=1 where id=1", (), True)
debe("salida correcta (cruza medianoche)", "update entradas_salidas_estadia set fecha_hora_salida='2026-11-16 06:00:00', usuario_salida_id=1 where id=1")
debe("RN-05: la celda liberada acepta otra estadía", "insert into entradas_salidas_estadia values (4,2,1,'2026-11-16 07:00:00',1,null,null)")
debe("RN-04: el vehículo que salió puede volver a entrar", "insert into entradas_salidas_estadia values (5,1,2,'2026-11-16 08:00:00',1,null,null)")
debe("novedad", "insert into novedades_novedad values (1,'RAYON','Rayón lateral','2026-11-16 08:30:00','2026-11-16 09:00:00',1)")
debe("novedad sin descripción rechazada", "insert into novedades_novedad values (2,'OTRO','   ','2026-11-16 08:30:00','2026-11-16 09:00:00',1)", (), True)
debe("novedad registrada antes de ocurrir rechazada", "insert into novedades_novedad values (3,'OTRO','x','2026-11-16 10:00:00','2026-11-16 09:00:00',1)", (), True)
debe("RN-14: novedad vinculada a la estadía 4", "insert into novedades_novedadestadia values (1,4)")
debe("RN-14: misma novedad vinculada a la estadía 5", "insert into novedades_novedadestadia values (1,5)")
debe("vínculo duplicado rechazado", "insert into novedades_novedadestadia values (1,5)", (), True)
debe("aviso 1 automático", "insert into notificaciones_avisocorreo values (1,1,1,'AUTOMATICO',null,'a@b.co','s','c',?,'ENVIADO_SIMULADO')", (d,))
debe("RN-11: segundo 'primer' correo rechazado", "insert into notificaciones_avisocorreo values (2,1,1,'MANUAL',1,'a@b.co','s','c',?,'ENVIADO_SIMULADO')", (d,), True)
debe("RN-22: reenvío manual", "insert into notificaciones_avisocorreo values (3,1,2,'MANUAL',1,'a@b.co','s','c',?,'ENVIADO_SIMULADO')", (d,))
debe("RN-22: segundo reenvío rechazado", "insert into notificaciones_avisocorreo values (4,1,3,'MANUAL',1,'a@b.co','s','c',?,'ENVIADO_SIMULADO')", (d,), True)
debe("intento fallido registrado sin número", "insert into notificaciones_avisocorreo values (5,1,null,'AUTOMATICO',null,'a@b.co','s','c',?,'FALLIDO')", (d,))
debe("manual sin usuario rechazado", "insert into notificaciones_avisocorreo values (6,1,null,'MANUAL',null,'a@b.co','s','c',?,'FALLIDO')", (d,), True)
debe("contacto con autoridades", "insert into notificaciones_contactoautoridad values (1,1,?,1,'Llamada a tránsito')", (d,))
debe("P-22: moto con placa antigua ABC12", "insert into usuarios_celdas_vehiculo values (5,'MNO45','MOTO','Honda','CB',2005,'Rojo',1,1,?)", (d,))
debe("P-22: placa en minúsculas rechazada", "insert into usuarios_celdas_vehiculo values (6,'abc123','CARRO','M','N',2020,'Azul',1,1,?)", (d,), True)
debe("P-22: placa con formato inválido rechazada", "insert into usuarios_celdas_vehiculo values (7,'AB-1234','CARRO','M','N',2020,'Azul',1,1,?)", (d,), True)
debe("P-23: modelo (año) fuera de rango rechazado", "insert into usuarios_celdas_vehiculo values (8,'JKL987','CARRO','M','N',1800,'Azul',1,1,?)", (d,), True)
debe("P-25: segundo contacto con autoridades del mismo vencimiento", "insert into notificaciones_contactoautoridad values (2,1,?,1,'Seguimiento')", (d,))
debe("RN-30: celular válido de otro propietario", "insert into usuarios_celdas_propietario values (4,'Luis Mora','1056789012','3109876543','l@m.co','Calle 1',1,?)", (d,))
debe("RN-30: teléfono fijo rechazado", "insert into usuarios_celdas_propietario values (5,'X Z','1067890123','6012345678','x@z.co','Calle 2',1,?)", (d,), True)
debe("RN-30: celular de 9 dígitos rechazado", "insert into usuarios_celdas_propietario values (6,'X W','1078901234','300123456','x@w.co','Calle 3',1,?)", (d,), True)
debe("operador para horarios", "insert into cuentas_usuario values (2,'op','h','O','P','OPERADOR',1,?,null)", (d,))
debe("DEC-014: franja nocturna 22:00-06:00", "insert into cuentas_horariooperador values (1,2,5,'22:00','06:00')")
debe("DEC-014: franja con inicio igual al fin rechazada", "insert into cuentas_horariooperador values (2,2,1,'08:00','08:00')", (), True)
debe("RN-32: autorización fuera de turno", "insert into cuentas_autorizacionfueraturno values (1,2,1,'Cubre ausencia','2026-11-15 15:00','2026-11-15 19:00',?)", (d,))
debe("RN-32: autorización con fin anterior al inicio rechazada", "insert into cuentas_autorizacionfueraturno values (2,2,1,'x','2026-11-15 19:00','2026-11-15 15:00',?)", (d,), True)
debe("RN-32: autorizarse a sí mismo rechazado", "insert into cuentas_autorizacionfueraturno values (3,1,1,'x','2026-11-15 15:00','2026-11-15 19:00',?)", (d,), True)
debe("DEC-015: solicitud de cambio pendiente", "insert into usuarios_celdas_solicitudcambiopropietario values (1,1,1,4,'Venta',2,?,'PENDIENTE',null,null,null)", (d,))
debe("DEC-015: segunda solicitud pendiente del mismo vehículo rechazada", "insert into usuarios_celdas_solicitudcambiopropietario values (2,1,1,4,'Otra',2,?,'PENDIENTE',null,null,null)", (d,), True)
debe("DEC-015: cambio al mismo propietario rechazado", "insert into usuarios_celdas_solicitudcambiopropietario values (3,2,1,1,'x',2,?,'PENDIENTE',null,null,null)", (d,), True)
debe("DEC-015: aprobada sin quién la resolvió rechazada", "update usuarios_celdas_solicitudcambiopropietario set estado='APROBADA' where id=1", (), True)
debe("DEC-015: aprobación completa", "update usuarios_celdas_solicitudcambiopropietario set estado='APROBADA', resuelto_por_id=1, fecha_resolucion='2026-11-15 10:00' where id=1")
debe("DEC-015: historial del propietario anterior", "insert into usuarios_celdas_historialpropiedad values (1,1,1,'2026-05-01 08:00','2026-11-15 10:00')")
debe("DEC-015: historial con fin anterior al inicio rechazado", "insert into usuarios_celdas_historialpropiedad values (2,1,1,'2026-11-15 10:00','2026-05-01 08:00')", (), True)
debe("DEC-013: registro en la bitácora", "insert into bitacora_registrooperacion values (1,?,2,'MODIFICAR','PROPIETARIO',1,'Cambió el celular','{\"telefono\": [\"3001234567\", \"3009998877\"]}')", (d,))
debe("DEC-013: acción desconocida rechazada", "insert into bitacora_registrooperacion values (2,?,2,'BORRAR','PROPIETARIO',1,'x',null)", (d,), True)
debe("RN-07/FK: no se puede borrar un vehículo con estadías", "delete from usuarios_celdas_vehiculo where id=1", (), True)

plan = db.execute("explain query plan select id from entradas_salidas_estadia where vehiculo_id=1 and fecha_hora_salida is null").fetchall()
print("Plan de consulta (estadía abierta por vehículo):", plan[0][-1])
print(f"\nResultado: {ok} pasan, {fail} fallan")
sys.exit(1 if fail else 0)
