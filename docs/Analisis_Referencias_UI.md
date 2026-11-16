# Análisis de los diseños de referencia de la interfaz

**Autor:** Software Engineer
**Fecha:** 2026-11-15
**Imágenes:** `docs/referencias_ui/referencia_1.png` a `referencia_4.png` (entregadas por el equipo el 2026-11-15)
**Estado:** Solicitud de cambio CHG-002 **aprobada** por el equipo el 2026-11-15.

## 1. Qué se adopta sin cambios de diseño

Los diseños son compatibles con los mockups aprobados en cuanto al **contenido**, y se adoptan como **estilo visual** de toda la aplicación:

- Paleta verde oscuro y verde de acción, barra lateral, encabezado con fecha y hora y usuario (iniciales, nombre y rol), y tarjetas con pasos numerados ("01 · Buscar vehículo", "02 · Seleccionar celda").
- Inicio de sesión con panel de marca a la izquierda y mensaje de error genérico (cumple RNF-001).
- **Registrar entrada:** selección de la celda en una **cuadrícula** (disponible, ocupada, seleccionada) en lugar de una lista desplegable. Cumple RF-003 y RNF-005.
- **Registrar salida:** tarjetas de celda, hora de entrada y tiempo de permanencia, más las **novedades del ingreso** y el botón "Agregar novedad". Es compatible con RF-004 y RF-007.
- **Vehículos dentro:** tarjetas de ocupación por categoría, filtro, tabla paginada y acción "+ Novedad".
- **Historial:** filtros, número de novedades por ingreso y panel con las novedades del ingreso seleccionado.
- Estados vacíos ("No hay vehículos dentro", "No se encontraron resultados").

Las pantallas que no están en las referencias (Novedades, Vencidos, Operadores, correo simulado y contacto con autoridades) se construirán con el **mismo estilo**, respetando los mockups M-07 a M-12.

## 2. Diferencias con lo aprobado (requieren decisión)

| # | En la referencia | Lo aprobado | Propuesta del Ingeniero |
|---|---|---|---|
| 1 | Selector **"Sede actual: Bogotá · Principal"** | No existe el concepto de sede: es un solo parqueadero. | **Omitir el selector.** Mostrar solo "Autos Colombia". Agregar sedes cambiaría el alcance y el modelo de datos. |
| 2 | **"Cliente inactivo":** no se permite la entrada. | El propietario tiene el campo `activo` (modelo v1.1), pero ninguna regla dice qué pasa con la entrada si está inactivo. | **Agregar RN-24:** no se registra la entrada si el propietario o el vehículo están inactivos ("El cliente está INACTIVO…"). Es una regla nueva pequeña y el modelo ya la soporta. |
| 3 | Modal "Registrar novedad" con tipo **"Observación"**, **una sola placa**, y **sin fecha ni hora del hecho** (usa la hora actual). | Tipos aprobados: Accidente, Rayón, Caída, Daño, Otro. RN-14: una novedad puede tener **varios vehículos**. RF-007 y RN-16: se registra la **fecha y hora del hecho**. | Mantener el modal con su estilo, pero: **(a)** agregar el tipo **"Observación"** (cambia el `CHECK` de tipo; requiere aprobación); **(b)** agregar el campo de fecha y hora del hecho, con la hora actual por defecto; **(c)** permitir agregar más placas desde el modal, con la placa actual precargada. |
| 4 | Celdas **A-01 … A-24** (carros) y **M-01 … M-16** (motos) | RN-20: **150** celdas de carro/camioneta y **50** de moto. | Mantener 150 + 50. Usar los códigos **A-001 … A-150** y **M-01 … M-50**. Mostrar la cuadrícula por bloques de 24 celdas con paginación ("Zona A · 1 de 7") para que se vea como en la referencia. |
| 5 | "Operario · **Turno de tarde**" | Los horarios y turnos son de la iteración 2 (RF-107). | Mostrar solo el rol ("Operador" o "Administrador") hasta la iteración 2. |
| 6 | Menú lateral con 4 opciones | Los mockups aprobados tienen además Novedades, Vencidos y Operadores. | Agregar esas opciones al menú lateral con el mismo estilo. Operadores solo para el administrador. |

## 3. Solicitud de cambio CHG-002

**Problema detectado:** los diseños de referencia introducen elementos que no están en los requerimientos aprobados (puntos 2 y 3a) o que los contradicen (puntos 1, 3b, 3c, 4 y 5).

**Cambio propuesto:** adoptar el estilo de las referencias con las propuestas de la tabla anterior.

**Artefactos afectados si se aprueba:**
- Requerimientos: nueva RN-24; tipo de novedad "Observación" en RF-007.
- Modelo de datos: el `CHECK` del tipo de novedad incluye `OBSERVACION`; el DDL pasa a v1.2.
- Mockups: se agrega una nota de que el estilo visual final sigue las referencias.
- Código: una nueva migración.

**Impacto:** bajo. No cambia la arquitectura ni las tablas, solo una restricción y una validación.

**Estado:** Aprobada (2026-11-15).
