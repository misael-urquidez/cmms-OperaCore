SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP DATABASE IF EXISTS operacore;
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
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: EDO_REFACCION
CREATE TABLE EDO_REFACCION (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
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
    telefono        VARCHAR(15)  NOT NULL UNIQUE,
    dirCalle        VARCHAR(100) NOT NULL,
    dirCodigoPostal VARCHAR(5)   NOT NULL,
    dirNumero       VARCHAR(10)  NOT NULL
) ENGINE=InnoDB;

-- Tabla: MARCA
-- CAMBIO: la PK se llama ahora "clave" (antes "codigo")
CREATE TABLE MARCA (
    clave           VARCHAR(10)  PRIMARY KEY,
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


-- Tabla: TIPO_FALLA
CREATE TABLE TIPO_FALLA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_SEVERIDAD
CREATE TABLE TIPO_SEVERIDAD (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(30)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: EDO_REPORTE
CREATE TABLE EDO_REPORTE (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_MANTENIMIENTO
CREATE TABLE TIPO_MANTENIMIENTO (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: ESTADO_ORDEN
CREATE TABLE ESTADO_ORDEN (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
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
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TIPO_HERRAMIENTA
CREATE TABLE TIPO_HERRAMIENTA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

-- Tabla: TAREAS
-- CAMBIO: ya no tiene FK directa a orden_mantenimiento (esa relación
-- ahora vive solo en la tabla puente TAREA_ORDEN). También cambian sus
-- columnas: nombre/descripcion/tiempoEstimado -> instruccion/actividad.
-- Al no depender de nada, se crea aquí, junto con los demás catálogos.
CREATE TABLE TAREAS (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    instruccion     VARCHAR(100) NOT NULL,
    actividad       BOOLEAN NOT NULL DEFAULT TRUE
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
    CONSTRAINT fk_modelo_marca FOREIGN KEY (marca) REFERENCES MARCA(clave)
) ENGINE=InnoDB;

-- Tabla: REFACCION
-- CAMBIO: se agregan nombre, codigoSku y puntoReorden
CREATE TABLE REFACCION (
    numeroRegistro   INT AUTO_INCREMENT PRIMARY KEY,
    nombre           VARCHAR(30) NOT NULL UNIQUE,
    codigoSku        VARCHAR(30) NOT NULL UNIQUE,
    puntoReorden     INT NULL,
    codigoInventario VARCHAR(30) NOT NULL UNIQUE,
    numeroOrden      VARCHAR(20) NOT NULL UNIQUE,
    costo            float NOT NULL,
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
-- CAMBIO: contrasena -> contraseña, se agrega actividad
CREATE TABLE TRABAJADOR (
    numeroNomina    VARCHAR(15)  PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL,
    apellidoPat     VARCHAR(50)  NOT NULL,
    apellidoMat     VARCHAR(50)  NULL,
    telefono        VARCHAR(15)  NOT NULL UNIQUE,
    correo          VARCHAR(100) NOT NULL UNIQUE,
    usuario         VARCHAR(30)  NOT NULL UNIQUE,
    `contraseña`    VARCHAR(255) NOT NULL,
    actividad       BOOLEAN NOT NULL DEFAULT TRUE,
    rol             VARCHAR(5)   NULL,
    especialidad    VARCHAR(5)   NULL,
    CONSTRAINT fk_trabajador_rol FOREIGN KEY (rol) REFERENCES ROL(codigo),
    CONSTRAINT fk_trabajador_especialidad FOREIGN KEY (especialidad) REFERENCES ESPECIALIDAD(codigo)
) ENGINE=InnoDB;

-- Tabla: HERRAMIENTA
-- CAMBIO: se quita cantidadDisponible, se agrega imagen.
-- [REVISAR CON EL EQUIPO] El diccionario pone tipo_herramienta como
-- Texto(5), pero TIPO_HERRAMIENTA.numeroRegistro sigue siendo INT
-- autoincremental. Lo dejo como INT para no romper la FK; si el equipo
-- quiere de verdad un código de texto, hay que agregarle a
-- TIPO_HERRAMIENTA una columna "codigo" VARCHAR y usar esa.
CREATE TABLE HERRAMIENTA (
    numeroRegistro   INT AUTO_INCREMENT PRIMARY KEY,
    nombre             VARCHAR(100) NOT NULL UNIQUE,
    descripcion        VARCHAR(255) NULL,
    imagen             VARCHAR(255) NULL,
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
    -- telefono        VARCHAR(15)  NOT NULL UNIQUE,
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
    herramienta      INT NOT NULL,
    edo_herramienta  VARCHAR(5)  NOT NULL,
    cantidad         INT NOT NULL DEFAULT 0,
    PRIMARY KEY (herramienta, edo_herramienta),
    CONSTRAINT fk_estherr_herramienta FOREIGN KEY (herramienta) REFERENCES HERRAMIENTA(numeroRegistro),
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
    CONSTRAINT fk_maquina_marca FOREIGN KEY (marca) REFERENCES MARCA(clave),
    CONSTRAINT fk_maquina_modelo FOREIGN KEY (modelo) REFERENCES MODELO(codigo),
    CONSTRAINT fk_maquina_estado FOREIGN KEY (estado_maquina) REFERENCES EDO_MAQUINA(codigo),
    CONSTRAINT fk_maquina_tipo FOREIGN KEY (tipo_maquina) REFERENCES TIPO_MAQUINA(numeroRegistro)
) ENGINE=InnoDB;

-- Tabla: INDICADOR
-- CAMBIO: ya no es catálogo de tipos de indicador. Ahora guarda los
-- resultados calculados (MTTR, MTBF, %disponibilidad) por máquina y
-- por periodo.
CREATE TABLE INDICADOR (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    fechaInicio     DATE NULL,
    fechaFin        DATE NULL,
    mttr            float NULL,
    mtbf            float NULL,
    porcentajeDispo INT NULL,
    maquina         VARCHAR(10) NULL,
    CONSTRAINT fk_indicador_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo)
) ENGINE=InnoDB;

-- =====================================================================
-- 5. TABLAS DE NIVEL 4 (dependen de tablas de nivel 3)
-- =====================================================================

-- Tabla: PIEZA
CREATE TABLE PIEZA (
    numeroSerie      VARCHAR(30)  PRIMARY KEY,
    codigoEtiqueta   VARCHAR(30)  NULL UNIQUE,
    nombre           VARCHAR(100) NOT NULL,
    costoInicial     float NOT NULL,
    horasOperacion   INT NOT NULL DEFAULT 0,
    tiempoVidaUtil   INT NOT NULL,
    depresacionAnual float NULL,
    valorResidual    float NULL,
    fechaInstalacion DATE NOT NULL,
    fechaGarantia    DATE NULL,
    edo_pieza     VARCHAR(5)  NULL,
    maquina          VARCHAR(10) NULL,
    tipo_pieza       INT NULL,
    CONSTRAINT fk_pieza_estado FOREIGN KEY (edo_pieza) REFERENCES EDO_PIEZA(codigo),
    CONSTRAINT fk_pieza_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_pieza_tipo FOREIGN KEY (tipo_pieza) REFERENCES TIPO_PIEZA(numeroRegistro)
) ENGINE=InnoDB;



-- Tabla: REGISTRO_OPS
-- CAMBIO: ya no referencia INDICADOR ni tiene "valor". Ahora guarda
-- las horas de operación acumuladas por máquina y periodo.
CREATE TABLE REGISTRO_OPS (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    fechaInicio     DATE NOT NULL,
    fechaFin        DATE NOT NULL,
    horasOperacion  INT NOT NULL,
    maquina         VARCHAR(10) NOT NULL,
    CONSTRAINT fk_regops_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo)
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
-- CAMBIO GRANDE: la PK ya no es "folio" (VARCHAR) sino "numeroRegistro"
-- (INT autoincremental). Se agregan asunto, fechaResolucion,
-- fechaCreacion, horaCreacion, tiempoParo, causaRaiz. Se eliminan
-- hora, tipo_reporte y estado_reporte.
CREATE TABLE REPORTE_FALLA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    asunto          VARCHAR(500) NOT NULL,
    fechaResolucion DATE NULL,
    fechaCreacion   DATE NOT NULL,
    horaCreacion    TIME NOT NULL,
    tiempoParo      INT NULL,
    causaRaiz       VARCHAR(500) NOT NULL,
    descripcion     VARCHAR(500) NULL,
    imagen          VARCHAR(255) NULL,
    maquina         VARCHAR(10) NOT NULL,
    trabajador      VARCHAR(15) NOT NULL,
    tipo_severidad  VARCHAR(5)  NOT NULL,
    estado_reporte VARCHAR(5)  NOT NULL,
    CONSTRAINT fk_repfalla_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_repfalla_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_repfalla_severidad FOREIGN KEY (tipo_severidad) REFERENCES TIPO_SEVERIDAD(codigo),
    CONSTRAINT fk_estado_reporte  FOREIGN KEY (estado_reporte) REFERENCES EDO_REPORTE(codigo); */

) ENGINE=InnoDB;


    /* CONSTRAINT fk_repfalla_tipofalla FOREIGN KEY (tipo_falla) REFERENCES TIPO_FALLA(numeroRegistro), */

    /* tipo_falla      INT  NOT NULL, */

/* ALTER TABLE REPORTE_FALLA ADD COLUMN estado_reporte VARCHAR(5) NULL;
ALTER TABLE REPORTE_FALLA ADD FOREIGN KEY (estado_reporte) REFERENCES EDO_REPORTE(codigo); */

CREATE TABLE TIPO_REPORTE (
    tipo_falla      INT NOT NULL,
    reporte_falla  INT  NOT NULL,
    PRIMARY KEY (tipo_falla, reporte_falla),
    CONSTRAINT fk_tiporep_tipofalla FOREIGN KEY (tipo_falla) REFERENCES TIPO_FALLA(numeroRegistro),
    CONSTRAINT fk_tiporep_reportefalla FOREIGN KEY (reporte_falla) REFERENCES REPORTE_FALLA(numeroRegistro)
) ENGINE=InnoDB;

-- =====================================================================
-- 6. TABLAS DE NIVEL 5 (dependen de tablas de nivel 4)
-- =====================================================================

-- Tabla: ORDEN_MANTENIMIENTO
-- CAMBIO: reporte_falla ahora es INT (antes VARCHAR(15)), porque
-- REPORTE_FALLA cambió su PK a numeroRegistro (INT).
CREATE TABLE ORDEN_MANTENIMIENTO (
    folio               VARCHAR(15) PRIMARY KEY,
    descripcion         VARCHAR(500) NOT NULL,
    diagnostico         VARCHAR(500) NULL,
    notas               VARCHAR(500) NULL,
    fechaProgramada     DATE NULL, -- NULL
    fechaCreacion       DATE NOT NULL,
    horaCreacion        TIME NOT NULL,
    fechaCierre         DATE NULL,
    horaCierre          TIME NULL,
    horasIntervenidas   float NULL,
    porcentaje float null,
    imagen              VARCHAR(255) NULL,
    maquina             VARCHAR(10) NULL,
    trabajador          VARCHAR(15) NULL,
    reporte_falla       INT NULL,
    tipo_mantenimiento  VARCHAR(5)  NULL,
    estado_orden        VARCHAR(5)  NULL, -- Falta porcentaje
    CONSTRAINT fk_orden_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_orden_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_orden_reportefalla FOREIGN KEY (reporte_falla) REFERENCES REPORTE_FALLA(numeroRegistro),
    CONSTRAINT fk_orden_tipomant FOREIGN KEY (tipo_mantenimiento) REFERENCES TIPO_MANTENIMIENTO(codigo),
    CONSTRAINT fk_orden_estado FOREIGN KEY (estado_orden) REFERENCES ESTADO_ORDEN(codigo)
) ENGINE=InnoDB;

-- Tabla: MOVIMIENTO
-- CAMBIO: se quitan cantidad y herramienta, se agrega descripcion.
CREATE TABLE MOVIMIENTO (
    numeroRegistro      INT AUTO_INCREMENT PRIMARY KEY,
    descripcion         VARCHAR(255) NULL,
    fecha               DATE NOT NULL,
    hora                TIME NOT NULL,
    tipoMovimiento      VARCHAR(20) NOT NULL,
    orden_mantenimiento VARCHAR(15) NULL,
    refaccion           INT NULL,
    pieza               VARCHAR(30) NULL,
    CONSTRAINT fk_mov_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio),
    CONSTRAINT fk_mov_refaccion FOREIGN KEY (refaccion) REFERENCES REFACCION(numeroRegistro),
    CONSTRAINT fk_mov_pieza FOREIGN KEY (pieza) REFERENCES PIEZA(numeroSerie)
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
    fechaInicio date not null,
    fechaCierre date null,
    horaInicio time not null,
    horafin time null,
    verificacion boolean,
    observaciones varchar(250) null,
    PRIMARY KEY (tarea, orden_mantenimiento),
    CONSTRAINT fk_tareaord_tarea FOREIGN KEY (tarea) REFERENCES TAREAS(numeroRegistro),
    CONSTRAINT fk_tareaord_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

-- Tabla: HERRA_ORDEN
CREATE TABLE HERRA_ORDEN (
    herramienta         INT(10) NOT NULL,
    orden_mantenimiento VARCHAR(15) NOT NULL,
    PRIMARY KEY (herramienta, orden_mantenimiento),
    CONSTRAINT fk_herraord_herramienta FOREIGN KEY (herramienta) REFERENCES HERRAMIENTA(numeroRegistro),
    CONSTRAINT fk_herraord_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- ÍNDICES ADICIONALES PARA OPTIMIZACIÓN
-- =====================================================================
CREATE INDEX idx_orden_estado ON ORDEN_MANTENIMIENTO(estado_orden);
CREATE INDEX idx_orden_fechaprog ON ORDEN_MANTENIMIENTO(fechaProgramada);
CREATE INDEX idx_repfalla_fecharesolucion ON REPORTE_FALLA(fechaResolucion);
CREATE INDEX idx_repfalla_fechacreacion ON REPORTE_FALLA(fechaCreacion);
CREATE INDEX idx_maquina_linea ON MAQUINA(linea);
CREATE INDEX idx_refaccion_stock ON REFACCION(stock);
CREATE INDEX idx_movimiento_fecha ON MOVIMIENTO(fecha);
CREATE INDEX idx_pieza_maquina ON PIEZA(maquina);
CREATE INDEX idx_indicador_maquina ON INDICADOR(maquina);
CREATE INDEX idx_registroops_maquina ON REGISTRO_OPS(maquina);

-- =====================================================================
-- FIN DEL SCRIPT
-- =====================================================================
