-- =====================================================================
-- Parqueadero "Autos Colombia" - Modelo físico v1 (SQLite 3)
-- Estado: v1.1 APROBADO el 2026-11-15 (docs/Modelo_Datos_v1.md)
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

-- Iteración 2 (RF-107). PROVISIONAL: atributos a confirmar en esa iteración.
CREATE TABLE cuentas_horariooperador (
    id              INTEGER      PRIMARY KEY AUTOINCREMENT,
    operador_id     INTEGER      NOT NULL REFERENCES cuentas_usuario (id) ON DELETE RESTRICT,
    dia_semana      SMALLINT     NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    hora_inicio     TIME         NOT NULL,
    hora_fin        TIME         NOT NULL,
    CHECK (hora_inicio <> hora_fin)
);
CREATE INDEX idx_horario_operador ON cuentas_horariooperador (operador_id);

-- -------------------------------------------------------- usuarios_celdas
CREATE TABLE usuarios_celdas_propietario (
    id                INTEGER      PRIMARY KEY AUTOINCREMENT,
    nombre_completo   VARCHAR(150) NOT NULL,
    numero_documento  VARCHAR(10)  NOT NULL UNIQUE        -- cédula de ciudadanía (P-23)
                      CHECK (numero_documento NOT GLOB '*[^0-9]*'
                             AND length(numero_documento) BETWEEN 5 AND 10),
    telefono          VARCHAR(20)  NOT NULL,
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
    tipo                  VARCHAR(10)  NOT NULL
                          CHECK (tipo IN ('ACCIDENTE', 'RAYON', 'CAIDA', 'DANO', 'OTRO')),
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
