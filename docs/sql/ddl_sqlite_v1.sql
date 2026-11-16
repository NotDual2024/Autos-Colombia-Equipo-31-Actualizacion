-- =====================================================================
-- Parqueadero "Autos Colombia" - Modelo físico v1 (SQLite 3)
-- Estado: v1.3 APROBADO el 2026-11-15 (iteración 2: bitácora, horarios, autorizaciones, cambio de propietario).
--
-- Este script documenta y valida el diseño. En la implementación, las
-- tablas las crean las migraciones de Django a partir de los modelos, que
-- deben reproducir exactamente estas columnas, restricciones e índices.
-- Los nombres siguen la convención de Django: <modulo>_<entidad>.
-- =====================================================================
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- cuentas
-- Usuario del sistema. En Django extiende AbstractUser; aquí solo se
-- listan las columnas que usa el dominio.
CREATE TABLE cuentas_usuario (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(150) NOT NULL UNIQUE,
    password        VARCHAR(128) NOT NULL,              -- hash Argon2 (DEC-012)
    first_name      VARCHAR(150) NOT NULL,
    last_name       VARCHAR(150) NOT NULL,
    rol             VARCHAR(15)  NOT NULL
                    CHECK (rol IN ('ADMINISTRADOR', 'OPERADOR')),
    is_active       BOOLEAN      NOT NULL DEFAULT 1,     -- RF-106: desactivar, nunca borrar
    date_joined     DATETIME     NOT NULL,
    last_login      DATETIME     NULL
);

-- Franjas de trabajo por día (RF-107, DEC-014). dia_semana: 1 = lunes ... 7 = domingo.
-- Si hora_fin < hora_inicio, la franja cruza la medianoche (RN-36).
-- Que no se crucen dos franjas del mismo día (RN-37) se valida en el servicio.
CREATE TABLE cuentas_horariooperador (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    operador_id     INTEGER      NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    dia_semana      SMALLINT     NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    hora_inicio     TIME         NOT NULL,
    hora_fin        TIME         NOT NULL,
    CHECK (hora_inicio <> hora_fin)
);
CREATE INDEX idx_horario_operador ON cuentas_horariooperador (operador_id, dia_semana);

-- Autorización para ingresar fuera de turno (RF-110, RN-32, DEC-014).
CREATE TABLE cuentas_autorizacionfueraturno (
    id                 INTEGER   PRIMARY KEY AUTOINCREMENT,
    operador_id        INTEGER   NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    autorizado_por_id  INTEGER   NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    motivo             TEXT      NOT NULL CHECK (length(trim(motivo)) > 0),
    desde              DATETIME  NOT NULL,
    hasta              DATETIME  NOT NULL,
    fecha_registro     DATETIME  NOT NULL,
    CHECK (hasta > desde),
    CHECK (operador_id <> autorizado_por_id)
);
CREATE INDEX idx_autorizacion_operador ON cuentas_autorizacionfueraturno (operador_id, hasta);

-- -------------------------------------------------------- usuarios_celdas
CREATE TABLE usuarios_celdas_propietario (
    id                INTEGER      PRIMARY KEY AUTOINCREMENT,
    nombre_completo   VARCHAR(150) NOT NULL,
    numero_documento  VARCHAR(10)  NOT NULL UNIQUE        -- cédula de ciudadanía (P-23)
                      CHECK (numero_documento NOT GLOB '*[^0-9]*'
                             AND length(numero_documento) BETWEEN 5 AND 10),
    telefono          VARCHAR(10)  NOT NULL               -- celular colombiano (RN-30)
                      CHECK (telefono GLOB '3[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
    correo            VARCHAR(254) NOT NULL,             -- obligatorio (DEC-002)
    direccion         VARCHAR(200) NOT NULL,
    activo            BOOLEAN      NOT NULL DEFAULT 1,
    fecha_registro    DATETIME     NOT NULL
);

CREATE TABLE usuarios_celdas_vehiculo (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    placa           VARCHAR(6)   NOT NULL UNIQUE          -- mayúsculas, sin espacios (P-22)
                    CHECK (placa GLOB '[A-Z][A-Z][A-Z][0-9][0-9][0-9]'       -- carro / camioneta
                        OR placa GLOB '[A-Z][A-Z][A-Z][0-9][0-9][A-Z]'       -- moto
                        OR placa GLOB '[A-Z][A-Z][A-Z][0-9][0-9]'),          -- moto antigua
    tipo            VARCHAR(10)  NOT NULL CHECK (tipo IN ('MOTO', 'CARRO', 'CAMIONETA')),
    marca           VARCHAR(50)  NOT NULL,
    nombre          VARCHAR(50)  NOT NULL,                -- línea o referencia, p. ej. "Spark"
    modelo          SMALLINT     NOT NULL CHECK (modelo BETWEEN 1950 AND 2100),   -- año
    color           VARCHAR(30)  NOT NULL,
    propietario_id  INTEGER      NOT NULL REFERENCES usuarios_celdas_propietario (id) ON DELETE RESTRICT,
    activo          BOOLEAN      NOT NULL DEFAULT 1,
    fecha_registro  DATETIME     NOT NULL
);
CREATE INDEX idx_vehiculo_propietario ON usuarios_celdas_vehiculo (propietario_id);

-- Propietarios ANTERIORES de un vehículo (RN-33, DEC-015). El propietario actual está en
-- vehiculo.propietario_id; su fecha de inicio es el 'hasta' del último registro de esta tabla
-- (o la fecha de registro del vehículo si nunca cambió). Así no se duplica el dato (DM-09).
CREATE TABLE usuarios_celdas_historialpropiedad (
    id              INTEGER   PRIMARY KEY AUTOINCREMENT,
    vehiculo_id     INTEGER   NOT NULL REFERENCES usuarios_celdas_vehiculo (id) ON DELETE RESTRICT,
    propietario_id  INTEGER   NOT NULL REFERENCES usuarios_celdas_propietario (id) ON DELETE RESTRICT,
    desde           DATETIME  NOT NULL,
    hasta           DATETIME  NOT NULL,
    CHECK (hasta > desde)
);
CREATE INDEX idx_historial_vehiculo ON usuarios_celdas_historialpropiedad (vehiculo_id, hasta);

-- Solicitud de cambio de propietario (RF-109, RN-33, DEC-015).
CREATE TABLE usuarios_celdas_solicitudcambiopropietario (
    id                     INTEGER      PRIMARY KEY AUTOINCREMENT,
    vehiculo_id            INTEGER      NOT NULL REFERENCES usuarios_celdas_vehiculo (id) ON DELETE RESTRICT,
    propietario_actual_id  INTEGER      NOT NULL REFERENCES usuarios_celdas_propietario (id) ON DELETE RESTRICT,
    propietario_nuevo_id   INTEGER      NOT NULL REFERENCES usuarios_celdas_propietario (id) ON DELETE RESTRICT,
    motivo                 TEXT         NOT NULL CHECK (length(trim(motivo)) > 0),
    solicitado_por_id      INTEGER      NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    fecha_solicitud        DATETIME     NOT NULL,
    estado                 VARCHAR(10)  NOT NULL DEFAULT 'PENDIENTE'
                           CHECK (estado IN ('PENDIENTE', 'APROBADA', 'RECHAZADA')),
    resuelto_por_id        INTEGER      NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    fecha_resolucion       DATETIME     NULL,
    observacion            TEXT         NULL,
    CHECK (propietario_nuevo_id <> propietario_actual_id),
    CHECK ((estado = 'PENDIENTE') = (resuelto_por_id IS NULL)),
    CHECK ((resuelto_por_id IS NULL) = (fecha_resolucion IS NULL))
);
-- Solo una solicitud pendiente por vehículo.
CREATE UNIQUE INDEX uq_solicitud_pendiente
    ON usuarios_celdas_solicitudcambiopropietario (vehiculo_id) WHERE estado = 'PENDIENTE';

CREATE TABLE usuarios_celdas_celda (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    codigo          VARCHAR(10)  NOT NULL UNIQUE,         -- p. ej. C-001, M-001
    tipo            VARCHAR(15)  NOT NULL CHECK (tipo IN ('MOTO', 'CARRO_CAMIONETA')),
    activa          BOOLEAN      NOT NULL DEFAULT 1
);
CREATE INDEX idx_celda_tipo ON usuarios_celdas_celda (tipo, activa);

-- ------------------------------------------------------------------ pagos
CREATE TABLE pagos_tarifa (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    categoria       VARCHAR(15)  NOT NULL CHECK (categoria IN ('MOTO', 'CARRO_CAMIONETA')),
    valor           INTEGER      NOT NULL CHECK (valor > 0),   -- pesos colombianos (COP)
    vigente_desde   DATE         NOT NULL,
    UNIQUE (categoria, vigente_desde)
);

CREATE TABLE pagos_pago (
    id                INTEGER    PRIMARY KEY AUTOINCREMENT,
    vehiculo_id       INTEGER    NOT NULL REFERENCES usuarios_celdas_vehiculo (id) ON DELETE RESTRICT,
    periodo_inicio    DATE       NOT NULL,
    periodo_fin       DATE       NOT NULL,                -- fecha de vencimiento
    valor             INTEGER    NOT NULL CHECK (valor > 0),  -- copia de la tarifa al pagar
    fecha_pago        DATETIME   NOT NULL,
    registrado_por_id INTEGER    NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    CHECK (periodo_fin >= periodo_inicio)
);
CREATE INDEX idx_pago_vehiculo_fin ON pagos_pago (vehiculo_id, periodo_fin);

-- ------------------------------------------------------- entradas_salidas
CREATE TABLE entradas_salidas_estadia (
    id                    INTEGER  PRIMARY KEY AUTOINCREMENT,
    vehiculo_id           INTEGER  NOT NULL REFERENCES usuarios_celdas_vehiculo (id) ON DELETE RESTRICT,
    celda_id              INTEGER  NOT NULL REFERENCES usuarios_celdas_celda (id) ON DELETE RESTRICT,
    fecha_hora_entrada    DATETIME NOT NULL,
    usuario_entrada_id    INTEGER  NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    fecha_hora_salida     DATETIME NULL,
    usuario_salida_id     INTEGER  NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    CHECK (fecha_hora_salida IS NULL OR fecha_hora_salida > fecha_hora_entrada),
    CHECK ((fecha_hora_salida IS NULL) = (usuario_salida_id IS NULL))
);
-- RN-04: un vehículo tiene como máximo una estadía abierta.
CREATE UNIQUE INDEX uq_estadia_vehiculo_abierta
    ON entradas_salidas_estadia (vehiculo_id) WHERE fecha_hora_salida IS NULL;
-- RN-05: una celda tiene como máximo una estadía abierta.
CREATE UNIQUE INDEX uq_estadia_celda_abierta
    ON entradas_salidas_estadia (celda_id) WHERE fecha_hora_salida IS NULL;
CREATE INDEX idx_estadia_vehiculo_entrada ON entradas_salidas_estadia (vehiculo_id, fecha_hora_entrada);
CREATE INDEX idx_estadia_entrada ON entradas_salidas_estadia (fecha_hora_entrada);

-- -------------------------------------------------------------- novedades
CREATE TABLE novedades_novedad (
    id                    INTEGER      PRIMARY KEY AUTOINCREMENT,
    tipo                  VARCHAR(12)  NOT NULL
                          CHECK (tipo IN ('ACCIDENTE', 'RAYON', 'CAIDA', 'DANO', 'OBSERVACION', 'OTRO')),
    descripcion           TEXT         NOT NULL CHECK (length(trim(descripcion)) > 0),
    fecha_hora_ocurrencia DATETIME     NOT NULL,
    fecha_hora_registro   DATETIME     NOT NULL,
    registrado_por_id     INTEGER      NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    CHECK (fecha_hora_ocurrencia <= fecha_hora_registro)
);
CREATE INDEX idx_novedad_ocurrencia ON novedades_novedad (fecha_hora_ocurrencia);

-- Asociativa N:M entre novedad y estadía (RN-14, RN-16). El vehículo se
-- obtiene a través de la estadía.
CREATE TABLE novedades_novedadestadia (
    novedad_id  INTEGER NOT NULL REFERENCES novedades_novedad (id) ON DELETE RESTRICT,
    estadia_id  INTEGER NOT NULL REFERENCES entradas_salidas_estadia (id) ON DELETE RESTRICT,
    PRIMARY KEY (novedad_id, estadia_id)
);
CREATE INDEX idx_novedadestadia_estadia ON novedades_novedadestadia (estadia_id);

-- --------------------------------------------------------- notificaciones
-- Cada correo de retiro (simulado). El vencimiento se identifica por el
-- pago cuyo periodo_fin ya pasó (RN-11, RN-21, RN-22).
CREATE TABLE notificaciones_avisocorreo (
    id               INTEGER      PRIMARY KEY AUTOINCREMENT,
    pago_id          INTEGER      NOT NULL REFERENCES pagos_pago (id) ON DELETE RESTRICT,
    numero_envio     SMALLINT     NULL CHECK (numero_envio IN (1, 2)),   -- 1 = primero, 2 = reenvío
    origen           VARCHAR(10)  NOT NULL CHECK (origen IN ('AUTOMATICO', 'MANUAL')),
    enviado_por_id   INTEGER      NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    destinatario     VARCHAR(254) NOT NULL,               -- copia del correo al momento del envío
    asunto           VARCHAR(200) NOT NULL,
    cuerpo           TEXT         NOT NULL,
    fecha_hora       DATETIME     NOT NULL,
    resultado        VARCHAR(20)  NOT NULL CHECK (resultado IN ('ENVIADO_SIMULADO', 'FALLIDO')),
    CHECK ((origen = 'MANUAL') = (enviado_por_id IS NOT NULL)),
    CHECK ((resultado = 'ENVIADO_SIMULADO') = (numero_envio IS NOT NULL))
);
-- RN-11 y RN-22: como máximo un primer correo y un reenvío exitosos por vencimiento.
CREATE UNIQUE INDEX uq_aviso_envio
    ON notificaciones_avisocorreo (pago_id, numero_envio) WHERE numero_envio IS NOT NULL;

-- Contacto con autoridades (RF-011). Solo el administrador (control en la aplicación).
CREATE TABLE notificaciones_contactoautoridad (
    id                 INTEGER  PRIMARY KEY AUTOINCREMENT,
    pago_id            INTEGER  NOT NULL REFERENCES pagos_pago (id) ON DELETE RESTRICT,
    fecha_hora         DATETIME NOT NULL,
    registrado_por_id  INTEGER  NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    observacion        TEXT     NOT NULL CHECK (length(trim(observacion)) > 0)
);
CREATE INDEX idx_contacto_pago ON notificaciones_contactoautoridad (pago_id);

-- --------------------------------------------------------------- bitacora
-- Bitácora de operaciones (RF-111, RN-34, DEC-013). Polimórfica: entidad + entidad_id
-- identifican el registro afectado (sin clave foránea, porque apunta a varias tablas).
-- detalle guarda los cambios en JSON: {"campo": ["antes", "después"], ...}. Nunca se borra.
CREATE TABLE bitacora_registrooperacion (
    id           INTEGER      PRIMARY KEY AUTOINCREMENT,
    fecha_hora   DATETIME     NOT NULL,
    usuario_id   INTEGER      NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    accion       VARCHAR(25)  NOT NULL CHECK (accion IN (
                     'CREAR', 'MODIFICAR', 'ACTIVAR', 'INACTIVAR',
                     'SOLICITAR_CAMBIO', 'APROBAR_CAMBIO', 'RECHAZAR_CAMBIO',
                     'RESTABLECER_CLAVE', 'ASIGNAR_HORARIO', 'QUITAR_HORARIO',
                     'AUTORIZAR_FUERA_TURNO')),
    entidad      VARCHAR(20)  NOT NULL CHECK (entidad IN (
                     'PROPIETARIO', 'VEHICULO', 'OPERADOR', 'HORARIO',
                     'AUTORIZACION', 'SOLICITUD_CAMBIO')),
    entidad_id   INTEGER      NOT NULL,
    descripcion  VARCHAR(255) NOT NULL,
    detalle      TEXT         NULL
);
CREATE INDEX idx_bitacora_entidad ON bitacora_registrooperacion (entidad, entidad_id);
CREATE INDEX idx_bitacora_usuario_fecha ON bitacora_registrooperacion (usuario_id, fecha_hora);
CREATE INDEX idx_bitacora_fecha ON bitacora_registrooperacion (fecha_hora);
