-- =====================================================================
--  OPERACORE - CMMS (Computerized Maintenance Management System)
--  Motor: MySQL 8.0 / MariaDB 10.x (InnoDB, utf8mb4)
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS operacore
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE operacore;

-- =====================================================================
-- 1. CATÁLOGOS BASE (sin dependencias)
-- =====================================================================

-- Tabla: TIPO_PIEZA
CREATE TABLE TIPO_PIEZA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: EDO_PIEZA
CREATE TABLE EDO_PIEZA (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: EDO_REFACCION
CREATE TABLE EDO_REFACCION (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_REFACCION
CREATE TABLE TIPO_REFACCION (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: CLASIFICACION
CREATE TABLE CLASIFICACION (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: PROVEEDOR
CREATE TABLE PROVEEDOR (
    codigo          VARCHAR(10)  PRIMARY KEY,
    rfc             VARCHAR(13)  NOT NULL UNIQUE,
    razonSocial     VARCHAR(100) NOT NULL UNIQUE,
    nombreComercial VARCHAR(100) NOT NULL UNIQUE,
    telefono        VARCHAR(15)  NOT NULL UNIQUE,
    email           VARCHAR(100) NOT NULL UNIQUE,
    dirCalle        VARCHAR(100) NOT NULL,
    dirCodigoPostal VARCHAR(5)   NOT NULL,
    dirNumero       VARCHAR(10)  NOT NULL,
    contNombre      VARCHAR(50)  NOT NULL,
    contApellPat    VARCHAR(50)  NOT NULL,
    contApellMat    VARCHAR(50)  NULL
) ENGINE=InnoDB;

-- Tabla: PLANTA
CREATE TABLE PLANTA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    ubicacion       VARCHAR(150) NULL
) ENGINE=InnoDB;

-- Tabla: MARCA
CREATE TABLE MARCA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_MAQUINA
CREATE TABLE TIPO_MAQUINA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: EDO_MAQUINA
CREATE TABLE EDO_MAQUINA (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: INDICADOR
CREATE TABLE INDICADOR (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL,
    unidadMedida    VARCHAR(20)  NOT NULL
) ENGINE=InnoDB;

-- Tabla: ROL
CREATE TABLE ROL (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: ESPECIALIDAD
CREATE TABLE ESPECIALIDAD (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_REPORTE
CREATE TABLE TIPO_REPORTE (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_FALLA
CREATE TABLE TIPO_FALLA (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_SEVERIDAD
CREATE TABLE TIPO_SEVERIDAD (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(30)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: EDO_REPORTE
CREATE TABLE EDO_REPORTE (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_MANTENIMIENTO
CREATE TABLE TIPO_MANTENIMIENTO (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: ESTADO_ORDEN
CREATE TABLE ESTADO_ORDEN (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_MOVIMIENTO
CREATE TABLE TIPO_MOVIMIENTO (
    codigo          VARCHAR(5)   PRIMARY KEY,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: EDO_HERRAMIENTA
CREATE TABLE EDO_HERRAMIENTA (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_HERRAMIENTA
CREATE TABLE TIPO_HERRAMIENTA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- =====================================================================
-- 2. TABLAS DE NIVEL 1 (dependen solo de catálogos base)
-- =====================================================================

-- Tabla: AREA
CREATE TABLE AREA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    telefono        VARCHAR(15)  NOT NULL UNIQUE,
    planta          VARCHAR(10)  NOT NULL,
    CONSTRAINT fk_area_planta FOREIGN KEY (planta) REFERENCES PLANTA(codigo)
) ENGINE=InnoDB;

-- Tabla: MODELO
CREATE TABLE MODELO (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    marca           VARCHAR(10)  NOT NULL,
    CONSTRAINT fk_modelo_marca FOREIGN KEY (marca) REFERENCES MARCA(codigo)
) ENGINE=InnoDB;

-- Tabla: REFACCION
CREATE TABLE REFACCION (
    numeroRegistro   INT AUTO_INCREMENT PRIMARY KEY,
    codigoInventario VARCHAR(30) NOT NULL UNIQUE,
    numeroOrden      VARCHAR(20) NOT NULL UNIQUE,
    costo            DECIMAL(10,2) NOT NULL,
    tiempoEntregaApr INT NULL,
    stock            INT NOT NULL DEFAULT 0,
    stockMinimo      INT NOT NULL DEFAULT 0,
    proveedor        VARCHAR(10) NULL,
    tipo_refaccion   INT NULL,
    clasificacion    VARCHAR(10) NULL,
    CONSTRAINT fk_refaccion_proveedor FOREIGN KEY (proveedor) REFERENCES PROVEEDOR(codigo),
    CONSTRAINT fk_refaccion_tipo FOREIGN KEY (tipo_refaccion) REFERENCES TIPO_REFACCION(numeroRegistro),
    CONSTRAINT fk_refaccion_clasificacion FOREIGN KEY (clasificacion) REFERENCES CLASIFICACION(codigo)
) ENGINE=InnoDB;

-- Tabla: TRABAJADOR
CREATE TABLE TRABAJADOR (
    numeroNomina    VARCHAR(15)  PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    apellidoPat     VARCHAR(50)  NOT NULL,
    apellidoMat     VARCHAR(50)  NOT NULL,
    telefono        VARCHAR(15)  NULL,
    correo          VARCHAR(100) NULL UNIQUE,
    usuario         VARCHAR(30)  NULL UNIQUE,
    contrasena      VARCHAR(255) NOT NULL,
    rol             VARCHAR(5)   NULL,
    especialidad    VARCHAR(5)   NULL,
    CONSTRAINT fk_trabajador_rol FOREIGN KEY (rol) REFERENCES ROL(codigo),
    CONSTRAINT fk_trabajador_especialidad FOREIGN KEY (especialidad) REFERENCES ESPECIALIDAD(codigo)
) ENGINE=InnoDB;

-- Tabla: HERRAMIENTA
CREATE TABLE HERRAMIENTA (
    codigo             VARCHAR(10)  PRIMARY KEY,
    nombre             VARCHAR(100) NOT NULL,
    descripcion        VARCHAR(255) NULL,
    cantidadDisponible INT NOT NULL DEFAULT 0,
    tipo_herramienta   INT NULL,
    CONSTRAINT fk_herramienta_tipo FOREIGN KEY (tipo_herramienta) REFERENCES TIPO_HERRAMIENTA(numeroRegistro)
) ENGINE=InnoDB;

-- =====================================================================
-- 3. TABLAS DE NIVEL 2 (dependen de tablas de nivel 1)
-- =====================================================================

-- Tabla: LINEA
CREATE TABLE LINEA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    area            VARCHAR(10)  NOT NULL,
    CONSTRAINT fk_linea_area FOREIGN KEY (area) REFERENCES AREA(codigo)
) ENGINE=InnoDB;

-- Tabla: ESTADO_REFACCION
CREATE TABLE ESTADO_REFACCION (
    estado_refaccion VARCHAR(5) NOT NULL,
    refaccion        INT NOT NULL,
    cantidad         INT NOT NULL DEFAULT 0,
    PRIMARY KEY (estado_refaccion, refaccion),
    CONSTRAINT fk_estref_edo FOREIGN KEY (estado_refaccion) REFERENCES EDO_REFACCION(codigo),
    CONSTRAINT fk_estref_refaccion FOREIGN KEY (refaccion) REFERENCES REFACCION(numeroRegistro)
) ENGINE=InnoDB;

-- Tabla: ESTADO_HERRAMIENTA
CREATE TABLE ESTADO_HERRAMIENTA (
    herramienta      VARCHAR(10) NOT NULL,
    edo_herramienta  VARCHAR(5)  NOT NULL,
    cantidad         INT NOT NULL DEFAULT 0,
    PRIMARY KEY (herramienta, edo_herramienta),
    CONSTRAINT fk_estherr_herramienta FOREIGN KEY (herramienta) REFERENCES HERRAMIENTA(codigo),
    CONSTRAINT fk_estherr_edo FOREIGN KEY (edo_herramienta) REFERENCES EDO_HERRAMIENTA(codigo)
) ENGINE=InnoDB;

-- =====================================================================
-- 4. TABLAS DE NIVEL 3 (dependen de tablas de nivel 2)
-- =====================================================================

-- Tabla: MAQUINA
CREATE TABLE MAQUINA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    numeroSerie     VARCHAR(30)  NULL UNIQUE,
    nombre          VARCHAR(100) NOT NULL,
    descripcion     VARCHAR(255) NULL,
    imagen_url      VARCHAR(255) NULL,
    fechaInstalacion DATE NOT NULL,
    linea           VARCHAR(10)  NULL,
    marca           VARCHAR(10)  NULL,
    modelo          VARCHAR(10)  NULL,
    estado_maquina  VARCHAR(5)   NULL,
    tipo_maquina    INT NULL,
    CONSTRAINT fk_maquina_linea FOREIGN KEY (linea) REFERENCES LINEA(codigo),
    CONSTRAINT fk_maquina_marca FOREIGN KEY (marca) REFERENCES MARCA(codigo),
    CONSTRAINT fk_maquina_modelo FOREIGN KEY (modelo) REFERENCES MODELO(codigo),
    CONSTRAINT fk_maquina_estado FOREIGN KEY (estado_maquina) REFERENCES EDO_MAQUINA(codigo),
    CONSTRAINT fk_maquina_tipo FOREIGN KEY (tipo_maquina) REFERENCES TIPO_MAQUINA(numeroRegistro)
) ENGINE=InnoDB;

-- =====================================================================
-- 5. TABLAS DE NIVEL 4 (dependen de tablas de nivel 3)
-- =====================================================================

-- Tabla: PIEZA
CREATE TABLE PIEZA (
    numeroSerie      VARCHAR(30)  PRIMARY KEY,
    codigoEtiqueta   VARCHAR(30)  NULL UNIQUE,
    nombre           VARCHAR(100) NOT NULL,
    costoInicial     DECIMAL(10,2) NOT NULL,
    horasOperacion   INT NOT NULL DEFAULT 0,
    tiempoVidaUtil   INT NOT NULL,
    depresacionAnual DECIMAL(5,2) NULL,
    valorResidual    DECIMAL(10,2) NULL,
    fechaInstalacion DATE NOT NULL,
    fechaGarantia    DATE NULL,
    estado_pieza     VARCHAR(5)  NULL,
    maquina          VARCHAR(10) NULL,
    tipo_pieza       INT NULL,
    refaccion        INT NULL,
    CONSTRAINT fk_pieza_estado FOREIGN KEY (estado_pieza) REFERENCES EDO_PIEZA(codigo),
    CONSTRAINT fk_pieza_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_pieza_tipo FOREIGN KEY (tipo_pieza) REFERENCES TIPO_PIEZA(numeroRegistro),
    CONSTRAINT fk_pieza_refaccion FOREIGN KEY (refaccion) REFERENCES REFACCION(numeroRegistro)
) ENGINE=InnoDB;

-- Tabla: REGISTRO_OPS
CREATE TABLE REGISTRO_OPS (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    fecha           DATE NOT NULL,
    hora            TIME NOT NULL,
    valor           DECIMAL(10,2) NOT NULL,
    maquina         VARCHAR(10) NOT NULL,
    indicador       INT NOT NULL,
    CONSTRAINT fk_regops_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_regops_indicador FOREIGN KEY (indicador) REFERENCES INDICADOR(numeroRegistro)
) ENGINE=InnoDB;

-- Tabla: REFACC_MAQUI
CREATE TABLE REFACC_MAQUI (
    maquina         VARCHAR(10) NOT NULL,
    refaccion       INT NOT NULL,
    PRIMARY KEY (maquina, refaccion),
    CONSTRAINT fk_refmaq_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_refmaq_refaccion FOREIGN KEY (refaccion) REFERENCES REFACCION(numeroRegistro)
) ENGINE=InnoDB;

-- Tabla: REPORTE_FALLA
CREATE TABLE REPORTE_FALLA (
    folio           VARCHAR(15) PRIMARY KEY,
    fecha           DATE NOT NULL,
    hora            TIME NOT NULL,
    descripcion     VARCHAR(500) NOT NULL,
    imagen          VARCHAR(255) NULL,
    maquina         VARCHAR(10) NULL,
    trabajador      VARCHAR(15) NULL,
    tipo_falla      VARCHAR(5)  NULL,
    tipo_severidad  VARCHAR(5)  NULL,
    tipo_reporte    VARCHAR(5)  NULL,
    estado_reporte  VARCHAR(5)  NULL,
    CONSTRAINT fk_repfalla_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_repfalla_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_repfalla_tipofalla FOREIGN KEY (tipo_falla) REFERENCES TIPO_FALLA(codigo),
    CONSTRAINT fk_repfalla_severidad FOREIGN KEY (tipo_severidad) REFERENCES TIPO_SEVERIDAD(codigo),
    CONSTRAINT fk_repfalla_tiporeporte FOREIGN KEY (tipo_reporte) REFERENCES TIPO_REPORTE(codigo),
    CONSTRAINT fk_repfalla_estado FOREIGN KEY (estado_reporte) REFERENCES EDO_REPORTE(codigo)
) ENGINE=InnoDB;

-- =====================================================================
-- 6. TABLAS DE NIVEL 5 (dependen de tablas de nivel 4)
-- =====================================================================

-- Tabla: ORDEN_MANTENIMIENTO
CREATE TABLE ORDEN_MANTENIMIENTO (
    folio               VARCHAR(15) PRIMARY KEY,
    descripcion         VARCHAR(500) NOT NULL,
    diagnostico         VARCHAR(500) NULL,
    notas               VARCHAR(500) NULL,
    fechaProgramada     DATE NOT NULL,
    fechaCreacion       DATE NOT NULL,
    horaCreacion        TIME NOT NULL,
    fechaCierre         DATE NULL,
    horaCierre          TIME NULL,
    horasIntervenidas   DECIMAL(5,2) NULL,
    imagen              VARCHAR(255) NULL,
    maquina             VARCHAR(10) NULL,
    trabajador          VARCHAR(15) NULL,
    reporte_falla       VARCHAR(15) NULL,
    tipo_mantenimiento  VARCHAR(5)  NULL,
    estado_orden        VARCHAR(5)  NULL,
    CONSTRAINT fk_orden_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_orden_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_orden_reportefalla FOREIGN KEY (reporte_falla) REFERENCES REPORTE_FALLA(folio),
    CONSTRAINT fk_orden_tipomant FOREIGN KEY (tipo_mantenimiento) REFERENCES TIPO_MANTENIMIENTO(codigo),
    CONSTRAINT fk_orden_estado FOREIGN KEY (estado_orden) REFERENCES ESTADO_ORDEN(codigo)
) ENGINE=InnoDB;

-- Tabla: TAREAS (según diccionario tiene FK directa a orden_mantenimiento)
CREATE TABLE TAREAS (
    numeroRegistro      INT AUTO_INCREMENT PRIMARY KEY,
    nombre              VARCHAR(100) NOT NULL,
    descripcion         VARCHAR(255) NULL,
    tiempoEstimado      DECIMAL(5,2) NULL,
    orden_mantenimiento VARCHAR(15) NULL,
    CONSTRAINT fk_tareas_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

-- Tabla: MOVIMIENTO
CREATE TABLE MOVIMIENTO (
    numeroRegistro      INT AUTO_INCREMENT PRIMARY KEY,
    fecha               DATE NOT NULL,
    hora                TIME NOT NULL,
    tipoMovimiento      VARCHAR(20) NOT NULL,
    cantidad            INT NOT NULL,
    orden_mantenimiento VARCHAR(15) NULL,
    herramienta         VARCHAR(10) NULL,
    refaccion           INT NULL,
    CONSTRAINT fk_mov_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio),
    CONSTRAINT fk_mov_herramienta FOREIGN KEY (herramienta) REFERENCES HERRAMIENTA(codigo),
    CONSTRAINT fk_mov_refaccion FOREIGN KEY (refaccion) REFERENCES REFACCION(numeroRegistro)
) ENGINE=InnoDB;

-- =====================================================================
-- 7. TABLAS PUENTE (N:M)
-- =====================================================================

-- Tabla: TRABA_ORDE_PERSONAL
CREATE TABLE TRABA_ORDE_PERSONAL (
    trabajador          VARCHAR(15) NOT NULL,
    orden_mantenimiento VARCHAR(15) NOT NULL,
    PRIMARY KEY (trabajador, orden_mantenimiento),
    CONSTRAINT fk_top_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_top_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

-- Tabla: TAREA_ORDEN
CREATE TABLE TAREA_ORDEN (
    tarea               INT NOT NULL,
    orden_mantenimiento VARCHAR(15) NOT NULL,
    PRIMARY KEY (tarea, orden_mantenimiento),
    CONSTRAINT fk_tareaord_tarea FOREIGN KEY (tarea) REFERENCES TAREAS(numeroRegistro),
    CONSTRAINT fk_tareaord_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

-- Tabla: HERRA_ORDEN
CREATE TABLE HERRA_ORDEN (
    herramienta         VARCHAR(10) NOT NULL,
    orden_mantenimiento VARCHAR(15) NOT NULL,
    PRIMARY KEY (herramienta, orden_mantenimiento),
    CONSTRAINT fk_herraord_herramienta FOREIGN KEY (herramienta) REFERENCES HERRAMIENTA(codigo),
    CONSTRAINT fk_herraord_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- ÍNDICES ADICIONALES PARA OPTIMIZACIÓN
-- =====================================================================
CREATE INDEX idx_orden_estado ON ORDEN_MANTENIMIENTO(estado_orden);
CREATE INDEX idx_orden_fechaprog ON ORDEN_MANTENIMIENTO(fechaProgramada);
CREATE INDEX idx_repfalla_fecha ON REPORTE_FALLA(fecha);
CREATE INDEX idx_maquina_linea ON MAQUINA(linea);
CREATE INDEX idx_refaccion_stock ON REFACCION(stock);
CREATE INDEX idx_movimiento_fecha ON MOVIMIENTO(fecha);
CREATE INDEX idx_pieza_maquina ON PIEZA(maquina);

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================