-- Modelo relacional de Nübe Coffee Lab
-- Autor: Yilver Medina Urrea · Electiva VI Ciencia de Datos · CORHUILA 2026-B · Semana 6
-- Motor de referencia: SQLite (funciona igual en PostgreSQL/MySQL cambiando tipos menores)

PRAGMA foreign_keys = ON;

CREATE TABLE punto_venta (
    id_punto        INTEGER PRIMARY KEY,
    nombre          TEXT    NOT NULL,
    barrio          TEXT    NOT NULL
);

CREATE TABLE cliente (
    id_cliente      TEXT    PRIMARY KEY,          -- C001, C002...
    nombre          TEXT    NOT NULL,
    telefono        TEXT,
    fecha_registro  DATE    NOT NULL
);

CREATE TABLE producto (
    id_producto     TEXT    PRIMARY KEY,          -- P01, P02...
    nombre          TEXT    NOT NULL UNIQUE,
    categoria       TEXT    NOT NULL,
    precio          INTEGER NOT NULL CHECK (precio > 0)
);

CREATE TABLE insumo (
    id_insumo       TEXT    PRIMARY KEY,          -- I01, I02...
    nombre          TEXT    NOT NULL UNIQUE,
    unidad          TEXT    NOT NULL,             -- L, kg, und
    costo_unitario  INTEGER NOT NULL
);

CREATE TABLE calendario_clima (
    fecha           DATE    PRIMARY KEY,
    dia_semana      TEXT    NOT NULL,
    es_festivo      INTEGER NOT NULL CHECK (es_festivo IN (0, 1)),
    temp_max_c      REAL,
    lluvia_mm       REAL
);

CREATE TABLE venta (
    id_venta        INTEGER PRIMARY KEY,
    fecha           DATE    NOT NULL REFERENCES calendario_clima(fecha),
    hora            TEXT    NOT NULL,
    id_punto        INTEGER NOT NULL REFERENCES punto_venta(id_punto),
    id_cliente      TEXT             REFERENCES cliente(id_cliente),  -- NULL = cliente sin tarjeta
    canal           TEXT    NOT NULL CHECK (canal IN ('Mostrador', 'Domicilio')),
    medio_pago      TEXT    NOT NULL
);

-- Tabla intermedia N:M  venta <-> producto
CREATE TABLE detalle_venta (
    id_venta        INTEGER NOT NULL REFERENCES venta(id_venta),
    id_producto     TEXT    NOT NULL REFERENCES producto(id_producto),
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario INTEGER NOT NULL,             -- precio cobrado ese día (histórico)
    PRIMARY KEY (id_venta, id_producto)
);

-- Tabla intermedia N:M  producto <-> insumo
CREATE TABLE receta (
    id_producto     TEXT    NOT NULL REFERENCES producto(id_producto),
    id_insumo       TEXT    NOT NULL REFERENCES insumo(id_insumo),
    cantidad        REAL    NOT NULL CHECK (cantidad > 0),   -- en la unidad del insumo
    PRIMARY KEY (id_producto, id_insumo)
);
