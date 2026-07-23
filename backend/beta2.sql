-- =====================================================================
-- OperaCore CMMS — SCRIPT MAESTRO CONSOLIDADO
-- Reemplaza: beta.sql + monitoreo_fase1.sql + modelo.sql + avr.sql
-- (fallas_fix_tipo_reporte.sql queda OBSOLETO: TIPO_REPORTE ya nace
--  con columna `id` en este script, no hace falta correrlo aparte)
--
-- Uso: mysql -u <usuario> -p < beta_full.sql
-- Esto BORRA la base "operacore" y la recrea desde cero con todo:
-- esquema, catálogos, datos de prueba, módulo de monitoreo, rutas de
-- modelos 3D y tu usuario admin (za / za).
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP DATABASE IF EXISTS operacore;
CREATE DATABASE IF NOT EXISTS operacore
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE operacore;

-- =====================================================================
-- 1. CATÁLOGOS BASE (sin dependencias)
-- =====================================================================

CREATE TABLE TIPO_PIEZA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE EDO_PIEZA (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE EDO_REFACCION (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TIPO_REFACCION (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE CLASIFICACION (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

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

CREATE TABLE PLANTA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    telefono        VARCHAR(15)  NOT NULL UNIQUE,
    dirCalle        VARCHAR(100) NOT NULL,
    dirCodigoPostal VARCHAR(5)   NOT NULL,
    dirNumero       VARCHAR(10)  NOT NULL
) ENGINE=InnoDB;

-- Tabla: MARCA (PK = "clave")
CREATE TABLE MARCA (
    clave           VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TIPO_MAQUINA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE EDO_MAQUINA (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE ROL (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE ESPECIALIDAD (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TIPO_FALLA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TIPO_SEVERIDAD (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(30)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE EDO_REPORTE (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TIPO_MANTENIMIENTO (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE ESTADO_ORDEN (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TIPO_MOVIMIENTO (
    codigo          VARCHAR(5)   PRIMARY KEY,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE EDO_HERRAMIENTA (
    codigo          VARCHAR(5)   PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TIPO_HERRAMIENTA (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE TAREAS (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    instruccion     VARCHAR(100) NOT NULL,
    actividad       BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- =====================================================================
-- 2. TABLAS DE NIVEL 1 (dependen solo de catálogos base)
-- =====================================================================

CREATE TABLE AREA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    telefono        VARCHAR(15)  NOT NULL UNIQUE,
    planta          VARCHAR(10)  NOT NULL,
    CONSTRAINT fk_area_planta FOREIGN KEY (planta) REFERENCES PLANTA(codigo)
) ENGINE=InnoDB;

CREATE TABLE MODELO (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(50)  NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    marca           VARCHAR(10)  NOT NULL,
    CONSTRAINT fk_modelo_marca FOREIGN KEY (marca) REFERENCES MARCA(clave)
) ENGINE=InnoDB;

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
    especialidad    INT   NULL,
    CONSTRAINT fk_trabajador_rol FOREIGN KEY (rol) REFERENCES ROL(codigo),
    CONSTRAINT fk_trabajador_especialidad FOREIGN KEY (especialidad) REFERENCES ESPECIALIDAD(numeroRegistro)
) ENGINE=InnoDB;

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

CREATE TABLE LINEA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL UNIQUE,
    descripcion     VARCHAR(255) NULL,
    telefono        VARCHAR(15)  NULL,
    area            VARCHAR(10)  NOT NULL,
    CONSTRAINT fk_linea_area FOREIGN KEY (area) REFERENCES AREA(codigo)
) ENGINE=InnoDB;

CREATE TABLE ESTADO_REFACCION (
    estado_refaccion VARCHAR(5) NOT NULL,
    refaccion        INT NOT NULL,
    cantidad         INT NOT NULL DEFAULT 0,
    PRIMARY KEY (estado_refaccion, refaccion),
    CONSTRAINT fk_estref_edo FOREIGN KEY (estado_refaccion) REFERENCES EDO_REFACCION(codigo),
    CONSTRAINT fk_estref_refaccion FOREIGN KEY (refaccion) REFERENCES REFACCION(numeroRegistro)
) ENGINE=InnoDB;

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
-- Incluye ya YA INTEGRADAS las columnas de:
--   - modelo.sql       -> modelo_3d
--   - monitoreo_fase1.sql -> modo_monitoreo, umbral_vibracion, requiere_revision_preventiva
CREATE TABLE MAQUINA (
    codigo          VARCHAR(10)  PRIMARY KEY,
    numeroSerie     VARCHAR(30)  NULL UNIQUE,
    nombre          VARCHAR(100) NOT NULL,
    descripcion     VARCHAR(255) NULL,
    imagen_url      VARCHAR(255) NULL,
    modelo_3d       VARCHAR(255) NULL,
    fechaInstalacion DATE NOT NULL,
    linea           VARCHAR(10)  NULL,
    marca           VARCHAR(10)  NULL,
    modelo          VARCHAR(10)  NULL,
    estado_maquina  VARCHAR(5)   NULL,
    tipo_maquina    INT NULL,
    modo_monitoreo  ENUM('simulado', 'manual', 'iot') NOT NULL DEFAULT 'simulado',
    umbral_vibracion FLOAT NOT NULL DEFAULT 4.0,
    requiere_revision_preventiva BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_maquina_linea FOREIGN KEY (linea) REFERENCES LINEA(codigo),
    CONSTRAINT fk_maquina_marca FOREIGN KEY (marca) REFERENCES MARCA(clave),
    CONSTRAINT fk_maquina_modelo FOREIGN KEY (modelo) REFERENCES MODELO(codigo),
    CONSTRAINT fk_maquina_estado FOREIGN KEY (estado_maquina) REFERENCES EDO_MAQUINA(codigo),
    CONSTRAINT fk_maquina_tipo FOREIGN KEY (tipo_maquina) REFERENCES TIPO_MAQUINA(numeroRegistro)
) ENGINE=InnoDB;

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

-- Tabla: LECTURA_SENSOR (de monitoreo_fase1.sql)
CREATE TABLE LECTURA_SENSOR (
    numeroRegistro INT AUTO_INCREMENT PRIMARY KEY,
    maquina VARCHAR(10) NOT NULL,
    `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    origen ENUM('manual', 'simulado', 'iot') NOT NULL,
    vibracion FLOAT NOT NULL,
    golpe BOOLEAN NOT NULL DEFAULT FALSE,
    temperatura FLOAT NULL,
    CONSTRAINT fk_lectura_sensor_maquina
        FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    INDEX idx_lectura_sensor_maquina_timestamp (maquina, `timestamp`)
) ENGINE=InnoDB;

-- =====================================================================
-- 5. TABLAS DE NIVEL 4 (dependen de tablas de nivel 3)
-- =====================================================================

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

CREATE TABLE REGISTRO_OPS (
    numeroRegistro  INT AUTO_INCREMENT PRIMARY KEY,
    fechaInicio     DATE NOT NULL,
    fechaFin        DATE NOT NULL,
    horasOperacion  INT NOT NULL,
    maquina         VARCHAR(10) NOT NULL,
    CONSTRAINT fk_regops_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo)
) ENGINE=InnoDB;

CREATE TABLE REFACC_MAQUI (
    maquina         VARCHAR(10) NOT NULL,
    refaccion       INT NOT NULL,
    PRIMARY KEY (maquina, refaccion),
    CONSTRAINT fk_refmaq_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_refmaq_refaccion FOREIGN KEY (refaccion) REFERENCES REFACCION(numeroRegistro)
) ENGINE=InnoDB;

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
    estado_reporte  VARCHAR(5)  NOT NULL,
    CONSTRAINT fk_repfalla_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_repfalla_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_repfalla_severidad FOREIGN KEY (tipo_severidad) REFERENCES TIPO_SEVERIDAD(codigo),
    CONSTRAINT fk_estado_reporte  FOREIGN KEY (estado_reporte) REFERENCES EDO_REPORTE(codigo)
) ENGINE=InnoDB;

-- tipo_falla ya no vive en REPORTE_FALLA: es muchos-a-muchos vía TIPO_REPORTE.
CREATE TABLE TIPO_REPORTE (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    tipo_falla      INT NOT NULL,
    reporte_falla  INT  NOT NULL,
    UNIQUE KEY uq_tiporep_falla_reporte (tipo_falla, reporte_falla),
    CONSTRAINT fk_tiporep_tipofalla FOREIGN KEY (tipo_falla) REFERENCES TIPO_FALLA(numeroRegistro),
    CONSTRAINT fk_tiporep_reportefalla FOREIGN KEY (reporte_falla) REFERENCES REPORTE_FALLA(numeroRegistro)
) ENGINE=InnoDB;

-- =====================================================================
-- 6. TABLAS DE NIVEL 5 (dependen de tablas de nivel 4)
-- =====================================================================

CREATE TABLE ORDEN_MANTENIMIENTO (
    folio               VARCHAR(15) PRIMARY KEY,
    descripcion         VARCHAR(500) NOT NULL,
    diagnostico         VARCHAR(500) NULL,
    notas               VARCHAR(500) NULL,
    fechaProgramada     DATE NULL,
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
    estado_orden        VARCHAR(5)  NULL,
    CONSTRAINT fk_orden_maquina FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    CONSTRAINT fk_orden_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_orden_reportefalla FOREIGN KEY (reporte_falla) REFERENCES REPORTE_FALLA(numeroRegistro),
    CONSTRAINT fk_orden_tipomant FOREIGN KEY (tipo_mantenimiento) REFERENCES TIPO_MANTENIMIENTO(codigo),
    CONSTRAINT fk_orden_estado FOREIGN KEY (estado_orden) REFERENCES ESTADO_ORDEN(codigo)
) ENGINE=InnoDB;

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

CREATE TABLE TRABA_ORDE_PERSONAL (
    trabajador          VARCHAR(15) NOT NULL,
    orden_mantenimiento VARCHAR(15) NOT NULL,
    PRIMARY KEY (trabajador, orden_mantenimiento),
    CONSTRAINT fk_top_trabajador FOREIGN KEY (trabajador) REFERENCES TRABAJADOR(numeroNomina),
    CONSTRAINT fk_top_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

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

CREATE TABLE HERRA_ORDEN (
    herramienta         INT(10) NOT NULL,
    orden_mantenimiento VARCHAR(15) NOT NULL,
    PRIMARY KEY (herramienta, orden_mantenimiento),
    CONSTRAINT fk_herraord_herramienta FOREIGN KEY (herramienta) REFERENCES HERRAMIENTA(numeroRegistro),
    CONSTRAINT fk_herraord_orden FOREIGN KEY (orden_mantenimiento) REFERENCES ORDEN_MANTENIMIENTO(folio)
) ENGINE=InnoDB;

-- =====================================================================
-- ÍNDICES ADICIONALES
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
-- 8. DATOS DE PRUEBA (antes: datos_prueba.sql)
-- =====================================================================

INSERT INTO TIPO_PIEZA (nombre, descripcion) VALUES
('Cabezal', 'Cabezal de pickup para colocar componentes en PCB'),
('Motor', 'Motor eléctrico para impulsar mecanismos'),
('Sensor', 'Sensor de detección o medición'),
('Nozzle', 'Boquilla para succión de componentes'),
('Correa', 'Correa de transmisión para movimiento');

INSERT INTO EDO_PIEZA (codigo, nombre, descripcion) VALUES
('OPERA', 'Operativa', 'Pieza en condiciones normales de funcionamiento'),
('DEGRA', 'Degradada', 'Instalada pero con desgaste visible, próxima a reemplazarse'),
('FALLI', 'Fallida', 'Dejó de funcionar, genera reporte de falla'),
('ENREH', 'En Rehabilitacion', 'Desmontada y en proceso de reparación en taller'),
('BAJA', 'Baja', 'Sin funcionalidad, se desecha o chatarrea');

INSERT INTO EDO_REFACCION (codigo, nombre, descripcion) VALUES
('DISPO', 'Disponible', 'Refacción disponible en almacén'),
('ENREP', 'En Reparacion', 'El repuesto esta dañado o averiado, se encuentra siendo evaluado para volver a estar operando'),
('BAJA', 'Baja', 'El repuesto sufrió daños irreparables o quedó obsoleta'),
('CANIB', 'Canibalizada', 'La pieza que fue extraida de un equipo para ser utilizada temporalmente en otro equipo');

INSERT INTO TIPO_REFACCION (nombre, descripcion) VALUES
('Rodamiento', 'Rodamiento para ejes y motores'),
('Nozzle', 'Boquilla para succión de componentes SMT'),
('Sensor óptico', 'Sensor de detección óptica para alineación'),
('Correa de transmisión', 'Correa para transmisión de movimiento'),
('Motor servo', 'Motor servo de alta precisión');

INSERT INTO CLASIFICACION (codigo, nombre, descripcion) VALUES
('ALTAC', 'Alta Criticidad', 'Componentes esenciales para el funcionamiento de los equipos principales y cuya falla detiene por completo el proceso de producción'),
('MECRI', 'Mediana criticidad', 'Son componentes importantes para la operación, pero el equipo cuenta con redundancias (máquinas de respaldo) o existen soluciones alternativas en caso de avería'),
('BAJAC', 'Baja criticidad', 'Son artículos de apoyo no esenciales, repuestos de desgaste rápido o piezas de uso estándar que no impactan la producción');

INSERT INTO PROVEEDOR (codigo, rfc, razonSocial, nombreComercial, telefono, email, dirCalle, dirCodigoPostal, dirNumero, contNombre, contApellPat, contApellMat) VALUES
('PROV001', 'YAM850101ABC', 'Yamaha Motor de México S.A. de C.V.', 'Yamaha SMT', '5551234567', 'ventas@yamaha-smt.mx', 'Av. Industrial', '02870', '1500', 'Roberto', 'García', 'López'),
('PROV002', 'PAR850201DEF', 'Partes Industriales S.A. de C.V.', 'ParInd', '5559876544', 'ventas@parind.mx', 'Calle de la Industria', '02870', '500', 'Laura', 'Martínez', 'Sánchez');

INSERT INTO PLANTA (codigo, nombre, descripcion, telefono, dirCalle, dirCodigoPostal, dirNumero) VALUES
('PLT001', 'Planta EMS Central', 'Planta de ensamble de componentes de cómputo', '5551234500', 'Av. Insurgentes', '21211', '1500');

INSERT INTO MARCA (clave, nombre, descripcion) VALUES
('YAMHA', 'Yamaha', 'Fabricante japonés de máquinas SMT'),
('HELR', 'Heller', 'Fabricante de hornos de reflow industriales'),
('OMRN', 'Omron', 'Fabricante de sistemas de inspección óptica'),
('DMDE', 'DMDE', 'Fabricante de dispensadores de pasta de soldadura'),
('BRNS', 'Branson', 'Fabricante de transportadores industriales'),
('KYWR', 'Keysight', 'Fabricante de equipos de prueba electrónica');

INSERT INTO TIPO_MAQUINA (nombre, descripcion) VALUES
('Pick & Place', 'Máquina para colocar componentes electrónicos en PCB'),
('Horno Reflow', 'Horno para soldadura de componentes por temperatura controlada'),
('AOI', 'Automated Optical Inspection - Inspección óptica automatizada'),
('Dispensador de pasta', 'Máquina para aplicar pasta de soldadura en PCB'),
('Transportador', 'Sistema de transporte de PCBs entre estaciones'),
('Estación de prueba', 'Equipo para verificar funcionamiento de PCBs ensambladas');

INSERT INTO EDO_MAQUINA (codigo, nombre, descripcion) VALUES
('OPERA', 'Operativa', 'Máquina en condiciones normales de funcionamiento'),
('ESPER', 'En Espera', 'La máquina se encuentra en condiciones para operar, pero se requiere la intervencion del operador'),
('DESHA', 'Deshabilitada', 'La máquina se encuentra apagada o desconectada intencionalmente'),
('MANTE', 'En Mantenimiento', 'La máquina está detenida porque los técnicos estan realizando ajustes'),
('FALLO', 'En Falla', 'La máquina se detuvo de manera no planificada debido a un error');

INSERT INTO ROL (codigo, nombre, descripcion) VALUES
('TECNI', 'Técnico', 'Técnico de mantenimiento'),
('ADMIN', 'Administrador', 'Administrador del sistema con acceso total'),
('ENCLN', 'Encargado de línea', 'Encargado de línea de producción, validación de órdenes');

INSERT INTO ESPECIALIDAD (nombre, descripcion) VALUES
('Surface Mount Technology', 'Especialidad en tecnología de montaje superficial'),
('Ball Grid Array', 'Especialidad en componentes BGA'),
('Automated Optical Inspection', 'Especialidad en inspección óptica'),
('Mecánica', 'Especialidad en sistemas mecánicos');

INSERT INTO TIPO_FALLA (nombre, descripcion) VALUES
('Mecánica', 'Fallo en componentes mecánicos'),
('Eléctrica', 'Fallo en componentes eléctricos o electrónicos'),
('Neumática', 'Fallo en sistemas neumáticos'),
('Software', 'Fallo en software o controladores'),
('Óptica', 'Fallo en sistemas de visión o inspección óptica');

INSERT INTO TIPO_SEVERIDAD (codigo, nombre, descripcion) VALUES
('BAJA', 'Baja', 'Anomalia menor que no afecta la producción'),
('MEDIA', 'Media', 'Fallo que afecta parcialmente la operación, pero no detiene la producción'),
('ALTA', 'Alta', 'La máquina sigue funcionando, pero de manera deficiente o con capacidad muy reducida'),
('CRITI', 'Crítica', 'La máquina dejó de funcionar por completo. Alto riesgo de accidentes');

INSERT INTO EDO_REPORTE (codigo, nombre, descripcion) VALUES
('ABIER', 'Abierto', 'Reporte recién o parcialmente creado, sin atención'),
('ENATE', 'En Atención', 'El reporte esta siendo evaluado y se procedera con el mantenimiento correspondiente'),
('ENESP', 'En Espera', 'El diagnóstico esta listo, se requiere la asignacion de refacción, herramienta o técnico disponible'),
('RESUE', 'Resuelto', 'La falla fue atendida'),
('CERRA', 'Cerrado', 'Verificado y documentado completamente'),
('CANCE', 'Cancelado', 'Se determinó que no era una falla real o fue un falso positivo');

INSERT INTO TIPO_MANTENIMIENTO (codigo, nombre, descripcion) VALUES
('CORRE', 'Correctivo', 'Mantenimiento para corregir una falla existente'),
('PREVE', 'Preventivo', 'Mantenimiento programado para prevenir fallas'),
('PREDI', 'Predictivo', 'Mantenimiento basado en análisis de condición'),
('EMER', 'Emergencia', 'Mantenimiento de emergencia para fallas críticas');

INSERT INTO ESTADO_ORDEN (codigo, nombre, descripcion) VALUES
('SOLIC', 'Solicitada', 'Orden solicitada, la orden ha sido generada, pero aún no ha sido evaluada ni aprobada'),
('APROB', 'Aprobada', 'Orden aprobada, la solicitud ha sido revisada, se han evaluado las prioridades, y se han asignado los recursos necesarios'),
('PROGR', 'Programada', 'Orden programada, La orden cuenta con una fecha y hora especifica de inicio y finalización'),
('ENPRO', 'En Progreso', 'Los técnicos o especialistas han comenzado a ejecutar la intervención física en el equipo'),
('ESESP', 'En Espera', 'El trabajo se ha detenido temporalmente'),
('EJECU', 'Ejecutada', 'Orden ejecutada, el trabajo físico ha terminado'),
('CERRA', 'Cerrada', 'Orden cerrada, la orden está finalizada, revisada y archivada'),
('CANCE', 'Cancelada', 'Orden cancelada, la orden fue anulada por decisión operativa'),
('PENDI', 'Pendiente', 'Orden creada, pendiente de ejecución');

INSERT INTO TIPO_MOVIMIENTO (codigo, descripcion) VALUES
('INSTA', 'Instalación de refacción como pieza en máquina'),
('DESMO', 'Desmontaje de pieza de máquina'),
('REHA', 'Rehabilitación de pieza para reuso');

INSERT INTO EDO_HERRAMIENTA (codigo, nombre, descripcion) VALUES
('DISPO', 'Disponible', 'Herramienta lista para uso'),
('ENRE', 'En Reparación', 'Herramienta dañada, en proceso de reparación'),
('ENUSO', 'En Uso', 'La herramienta se encuentra ocupada'),
('BAJA', 'Baja', 'Herramienta sin posibilidad de reparación');

INSERT INTO TIPO_HERRAMIENTA (nombre, descripcion) VALUES
('Herramienta manual', 'Herramientas de uso manual como llaves y destornilladores'),
('Herramienta eléctrica', 'Herramientas motorizadas como taladros y atornilladores'),
('Instrumento de calibración', 'Instrumentos de precisión para calibración y medición');

INSERT INTO TAREAS (instruccion, actividad) VALUES
('Verificar alineación del cabezal', TRUE),
('Limpiar componentes y superficies', TRUE),
('Calibrar sensores de posición', TRUE),
('Inspeccionar conexiones eléctricas', TRUE),
('Lubricar mecanismos móviles', TRUE);

INSERT INTO AREA (codigo, nombre, descripcion, telefono, planta) VALUES
('ARR001', 'Área de Montaje SMT', 'Zona de ensamble superficial de componentes', '5551234568', 'PLT001'),
('ARR002', 'Área de Soldadura', 'Zona de soldadura por reflow y selección', '5551234569', 'PLT001'),
('ARR003', 'Área de Inspección', 'Zona de inspección óptica y prueba', '5551234570', 'PLT001');

INSERT INTO MODELO (codigo, nombre, descripcion, marca) VALUES
('YPK2', 'YPK Pick & Place', 'Modelo de alta velocidad para componentes 0201', 'YAMHA'),
('HLR6', 'Heller 600', 'Horno de reflow con 6 zonas de temperatura', 'HELR'),
('VT-S', 'VT-S730', 'Sistema de inspección óptica 3D', 'OMRN'),
('TFS6', 'TFS600', 'Dispensador de pasta de soldadura de alto volumen', 'DMDE'),
('CONV1', 'Conveyor 100', 'Transportador de banda continua', 'BRNS'),
('DMM3', 'DMM3000', 'Estación de prueba multicanal', 'KYWR');

INSERT INTO REFACCION (nombre, codigoSku, puntoReorden, codigoInventario, numeroOrden, costo, tiempoEntregaApr, stock, stockMinimo, proveedor, tipo_refaccion, clasificacion) VALUES
('Rodamiento 6205', 'SKU-6205-001', 5, 'INV-6205', 'ORD-2026-001', 125.50, 7, 15, 3, 'PROV001', 1, 'ALTAC'),
('Nozzle 0402', 'SKU-NZ0402', 10, 'INV-NZ0402', 'ORD-2026-002', 45.00, 5, 30, 8, 'PROV001', 2, 'ALTAC'),
('Sensor óptico PR10', 'SKU-SPR10', 3, 'INV-SPR10', 'ORD-2026-003', 320.00, 10, 6, 2, 'PROV002', 3, 'MECRI'),
('Correa HTD5M-500', 'SKU-CHT5M', 4, 'INV-CHT5M', 'ORD-2026-004', 85.00, 3, 10, 3, 'PROV001', 4, 'BAJAC'),
('Motor servo YSM40', 'SKU-MSY40', 2, 'INV-MSY40', 'ORD-2026-005', 890.00, 14, 4, 1, 'PROV002', 5, 'ALTAC');

-- TRABAJADOR (incluye ya tu usuario admin al final, antes: avr.sql)
INSERT INTO TRABAJADOR (numeroNomina, nombre, apellidoPat, apellidoMat, telefono, correo, usuario, `contraseña`, actividad, rol, especialidad) VALUES
('NOM-001', 'Juan', 'Pérez', 'García', '5559876543', 'juan.perez@ems.mx', 'jperez', 'password123', TRUE, 'TECNI', 1),
('NOM-002', 'María', 'López', 'Hernández', '5559876544', 'maria.lopez@ems.mx', 'mlopez', 'password123', TRUE, 'ENCLN', 1),
('NOM-003', 'Carlos', 'Ruiz', 'Martínez', '5559876545', 'carlos.ruiz@ems.mx', 'cruiz', 'password123', TRUE, 'TECNI', 4),
('NOM-004', 'Ana', 'García', 'Torres', '5559876546', 'ana.garcia@ems.mx', 'agarcia', 'password123', TRUE, 'ADMIN', 3),
('NOM001', 'Zacarías', 'Pérez', 'López', '6641234567', 'za@example.com', 'za', 'za', TRUE, 'ADMIN', NULL);

INSERT INTO HERRAMIENTA (nombre, descripcion, imagen, tipo_herramienta) VALUES
('Juego de llaves Allen', 'Juego de llaves Allen del #1 al #10', '/img/herramientas/llaves_allen.jpg', 1),
('Multímetro digital', 'Multímetro digital Fluke 87V para medición eléctrica', '/img/herramientas/multimetro.jpg', 2),
('Juego de calibración', 'Juego de bloques patrón y medidores de alineación', '/img/herramientas/calibracion.jpg', 3);

INSERT INTO LINEA (codigo, nombre, descripcion, area) VALUES
('LI001', 'Línea de Producción 1', 'Primera línea de ensamble SMT', 'ARR001'),
('LI002', 'Línea de Producción 2', 'Segunda línea de ensamble SMT', 'ARR001');

INSERT INTO ESTADO_REFACCION (estado_refaccion, refaccion, cantidad) VALUES
('DISPO', 1, 15),
('DISPO', 2, 30),
('ENREP', 3, 1),
('DISPO', 4, 10);

INSERT INTO ESTADO_HERRAMIENTA (herramienta, edo_herramienta, cantidad) VALUES
(1, 'DISPO', 5),
(2, 'DISPO', 3),
(3, 'ENRE', 1);

-- MAQUINA (incluye ya integradas las rutas modelo_3d, antes: modelo.sql)
INSERT INTO MAQUINA (codigo, numeroSerie, nombre, descripcion, imagen_url, modelo_3d, fechaInstalacion, linea, marca, modelo, estado_maquina, tipo_maquina) VALUES
('MAQ001', 'SN-YAM-YPK2-001', 'Pick & Place Principal', 'Máquina de alta velocidad para colocación de componentes SMT', 'images/YamahaYS12.png', 'images/YamahaYS12.glb', '2020-01-15', 'LI001', 'YAMHA', 'YPK2', 'OPERA', 1),
('MAQ002', 'SN-HEL-HLR6-001', 'Horno Reflow', 'Horno de reflow con 6 zonas de temperatura para soldadura', 'images/Heller1707MK5.png', 'images/Heller1707MK5.glb', '2019-06-20', 'LI001', 'HELR', 'HLR6', 'OPERA', 2),
('MAQ003', 'SN-OMR-VTS-001', 'AOI Inspector', 'Sistema de inspección óptica automatizada 3D', 'images/KohYoungZenithAlpha3D.png', 'images/KohYoungZenithAlpha3D.glb', '2021-03-10', 'LI002', 'OMRN', 'VT-S', 'MANTE', 3),
('MAQ004', 'SN-DMD-TFS6-001', 'Dispensador de Pasta', 'Dispensador de pasta de soldadura de alto volumen', 'images/DEKNeoHorizon03iX.png', 'images/DEKNeoHorizon03iX.glb', '2020-08-05', 'LI001', 'DMDE', 'TFS6', 'OPERA', 4),
('MAQ005', 'SN-BRN-CONV-001', 'Transportador Principal', 'Transportador de banda continua entre estaciones', 'images/JOTAutomationJ301-10.png', 'images/JOTAutomationJ301-10.glb', '2018-11-12', 'LI001', 'BRNS', 'CONV1', 'OPERA', 5),
('MAQ006', 'SN-KEY-DMM3-001', 'Estación de Prueba', 'Estación de prueba multicanal para verificación de PCBs', 'images/SeicaPilotV8.png', 'images/SeicaPilotV8.glb', '2022-02-28', 'LI002', 'KYWR', 'DMM3', 'FALLO', 6);

-- MAQ007 comentada para probar que el sistema la ignora
-- INSERT INTO MAQUINA (codigo, numeroSerie, nombre, descripcion, imagen_url, fechaInstalacion, linea, marca, modelo, estado_maquina, tipo_maquina) VALUES
-- ('MAQ007', 'SN-YAM-YPK2-002', 'Pick & Place Respaldo', 'Unidad de respaldo para alta demanda', '/img/maquinas/pick_place_02.jpg', '2019-09-01', 'LI002', 'YAMHA', 'YPK2', 'DESHA', 1);

INSERT INTO INDICADOR (fechaInicio, fechaFin, mttr, mtbf, porcentajeDispo, maquina) VALUES
('2026-01-01', '2026-01-31', 2.5, 104.0, 98, 'MAQ001'),
('2026-01-01', '2026-03-31', 4.0, 95.0, 96, 'MAQ002'),
('2026-01-01', '2026-03-31', 8.0, 150.0, 95, 'MAQ003'),
('2026-01-01', '2026-06-30', 2.0, 130.0, 98, 'MAQ004'),
('2026-01-01', '2026-06-30', 1.0, 200.0, 99, 'MAQ005'),
('2026-01-01', '2026-06-30', 6.0, 80.0, 93, 'MAQ006');

INSERT INTO PIEZA (numeroSerie, codigoEtiqueta, nombre, costoInicial, horasOperacion, tiempoVidaUtil, depresacionAnual, valorResidual, fechaInstalacion, fechaGarantia, edo_pieza, maquina, tipo_pieza) VALUES
('PS-6205-001', 'ETQ-6205-001', 'Rodamiento Cabezal Principal', 125.50, 2500, 10000, 10.05, 25.00, '2026-06-01', '2028-06-01', 'OPERA', 'MAQ001', 1),
('PS-SPR10-001', 'ETQ-SPR10-001', 'Sensor de temperatura zona 3', 320.00, 8500, 15000, 19.60, 26.00, '2021-03-10', '2024-03-10', 'OPERA', 'MAQ002', 3),
('PS-CAM-001', 'ETQ-CAM-001', 'Cámara AOI principal', 4500.00, 6000, 20000, 210.00, 300.00, '2021-03-10', '2024-03-10', 'FALLI', 'MAQ003', 3),
('PS-NZ0402-001', 'ETQ-NZ0402-001', 'Boquilla dispensadora #1', 45.00, 3200, 5000, 5.40, 18.00, '2023-01-15', '2025-01-15', 'OPERA', 'MAQ004', 4),
('PS-CHT5M-001', 'ETQ-CHT5M-001', 'Correa transportadora principal', 85.00, 12000, 8000, 7.50, 25.00, '2022-06-10', '2024-06-10', 'DEGRA', 'MAQ005', 5),
('PS-MSY40-001', 'ETQ-MSY40-001', 'Motor servo eje X', 890.00, 4200, 12000, 72.08, 25.00, '2022-02-28', '2025-02-28', 'OPERA', 'MAQ006', 2);

INSERT INTO REGISTRO_OPS (fechaInicio, fechaFin, horasOperacion, maquina) VALUES
('2026-01-01', '2026-01-31', 208, 'MAQ001'),
('2026-06-01', '2026-06-30', 195, 'MAQ001'),
('2026-01-01', '2026-01-31', 200, 'MAQ002'),
('2026-06-01', '2026-06-30', 195, 'MAQ002'),
('2026-01-01', '2026-01-31', 205, 'MAQ003'),
('2026-05-01', '2026-05-31', 120, 'MAQ003'),
('2026-01-01', '2026-01-31', 200, 'MAQ004'),
('2026-06-01', '2026-06-30', 185, 'MAQ004'),
('2026-01-01', '2026-01-31', 210, 'MAQ005'),
('2026-06-01', '2026-06-30', 205, 'MAQ005'),
('2026-01-01', '2026-01-31', 180, 'MAQ006'),
('2026-06-01', '2026-06-30', 80, 'MAQ006');

INSERT INTO REFACC_MAQUI (maquina, refaccion) VALUES
('MAQ001', 1),
('MAQ001', 2),
('MAQ002', 3),
('MAQ003', 3),
('MAQ004', 2),
('MAQ005', 4);

INSERT INTO REPORTE_FALLA (numeroRegistro, asunto, fechaResolucion, fechaCreacion, horaCreacion, tiempoParo, causaRaiz, descripcion, imagen, maquina, trabajador, tipo_severidad, estado_reporte) VALUES
(1, 'Ruido anormal en cabezal de pickup', '2026-01-20', '2026-01-20', '08:30:00', 2, 'Desgaste de rodamiento del eje principal', 'Se detectó ruido metálico al operar el cabezal a alta velocidad', '/img/reportes/ruido_cabezal.jpg', 'MAQ001', 'NOM-001', 'MEDIA', 'CERRA'),
(2, 'Temperatura inestable en zona 3', '2026-03-17', '2026-03-15', '10:15:00', 16, 'Termoparo dañado en zona 3 del horno', 'La temperatura oscilaba ±15°C impidiendo soldadura correcta', '/img/reportes/temp_inestable.jpg', 'MAQ002', 'NOM-003', 'ALTA', 'CERRA'),
(3, 'Error de imagen en inspección AOI', '2026-05-14', '2026-05-10', '07:45:00', 72, 'Falla en cámara principal del AOI', 'La cámara no logra enfocar correctamente, genera falsos positivos', '/img/reportes/error_aoi.jpg', 'MAQ003', 'NOM-001', 'ALTA', 'CERRA'),
(4, 'Fuga de pasta de soldadura', '2026-06-03', '2026-06-01', '09:00:00', 4, 'Boquilla desgastada en dispensador', 'Se observó fuga de pasta por la boquilla principal', '/img/reportes/fuga_pasta.jpg', 'MAQ004', 'NOM-003', 'MEDIA', 'CERRA'),
(5, 'Pantalla de control congelada', NULL, '2026-07-10', '14:20:00', NULL, 'Fallo en software de control de la estación', 'La pantalla táctil dejó de responder, equipo detenido completamente', '/img/reportes/pantalla_congelada.jpg', 'MAQ006', 'NOM-001', 'CRITI', 'ENATE');

INSERT INTO TIPO_REPORTE (tipo_falla, reporte_falla) VALUES
(1, 1),
(2, 2),
(5, 3),
(1, 4),
(3, 4),
(4, 5);

INSERT INTO ORDEN_MANTENIMIENTO (folio, descripcion, diagnostico, notas, fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre, horasIntervenidas, porcentaje, imagen, maquina, trabajador, reporte_falla, tipo_mantenimiento, estado_orden) VALUES
('OM-2026-001', 'Reemplazo de rodamiento en cabezal', 'Rodamiento 6205 con desgaste avanzado', 'Se reemplazó con refacción del almacén', '2026-01-22', '2026-01-20', '09:00:00', '2026-01-22', '11:30:00', 2.5, 100.00, '/img/ordenes/om_2026_001.jpg', 'MAQ001', 'NOM-001', 1, 'CORRE', 'PENDI'),
('OM-2026-002', 'Calibración de zona de temperatura', 'Termoparo dañado en zona 3', 'Se reemplazó termoparo y se calibraron las 6 zonas', '2026-03-16', '2026-03-15', '11:00:00', '2026-03-17', '03:00:00', 16.0, 100.00, '/img/ordenes/om_2026_002.jpg', 'MAQ002', 'NOM-003', 2, 'CORRE', 'CERRA'),
('OM-2026-003', 'Reemplazo de cámara AOI', 'Cámara principal con falla irreparable', 'Se instaló cámara de repuesto del almacén', '2026-05-12', '2026-05-10', '08:00:00', '2026-05-14', '07:45:00', 72.0, 100.00, '/img/ordenes/om_2026_003.jpg', 'MAQ003', 'NOM-001', 3, 'CORRE', 'CERRA'),
('OM-2026-004', 'Reemplazo de boquilla dispensadora', 'Boquilla desgastada por uso continuo', 'Se reemplazó boquilla y se verificó presión', '2026-06-02', '2026-06-01', '09:30:00', '2026-06-03', '01:00:00', 4.0, 100.00, '/img/ordenes/om_2026_004.jpg', 'MAQ004', 'NOM-003', 4, 'CORRE', 'CERRA'),
('OM-2026-005', 'Reparación de pantalla de control', 'Fallo en software de control', 'En espera de técnico especializado en software', '2026-07-15', '2026-07-11', '08:00:00', NULL, NULL, NULL, 25.00, '/img/ordenes/om_2026_005.jpg', 'MAQ006', 'NOM-001', 5, 'CORRE', 'ENPRO');

INSERT INTO MOVIMIENTO (numeroRegistro, descripcion, fecha, hora, tipoMovimiento, orden_mantenimiento, refaccion, pieza) VALUES
(1, 'Instalación de rodamiento 6205 en cabezal', '2026-01-22', '10:15:00', 'INSTA', 'OM-2026-001', 1, 'PS-6205-001'),
(2, 'Reemplazo de termoparo zona 3', '2026-03-16', '14:30:00', 'INSTA', 'OM-2026-002', 3, 'PS-CAM-001'),
(3, 'Retiro de cámara AOI dañada', '2026-05-12', '09:00:00', 'DESMO', 'OM-2026-003', NULL, 'PS-CAM-001'),
(4, 'Instalación de boquilla dispensadora', '2026-06-02', '10:00:00', 'INSTA', 'OM-2026-004', 2, 'PS-NZ0402-001');

INSERT INTO TRABA_ORDE_PERSONAL (trabajador, orden_mantenimiento) VALUES
('NOM-001', 'OM-2026-001'),
('NOM-003', 'OM-2026-002'),
('NOM-001', 'OM-2026-003'),
('NOM-003', 'OM-2026-004'),
('NOM-001', 'OM-2026-005');

INSERT INTO TAREA_ORDEN (tarea, orden_mantenimiento, fechaInicio, fechaCierre, horaInicio, horafin, verificacion, observaciones) VALUES
(1, 'OM-2026-001', '2026-01-22', '2026-01-22', '09:30:00', '11:00:00', TRUE, 'Verificación exitosa, alineación correcta'),
(2, 'OM-2026-002', '2026-03-16', '2026-03-16', '14:00:00', '16:00:00', TRUE, 'Limpieza de zona completada'),
(3, 'OM-2026-002', '2026-03-17', '2026-03-17', '01:00:00', '03:00:00', TRUE, 'Calibración verificada con termoparo patrón'),
(4, 'OM-2026-003', '2026-05-12', '2026-05-14', '09:00:00', '07:45:00', TRUE, 'Cámara instalada y calibrada correctamente'),
(5, 'OM-2026-004', '2026-06-02', '2026-06-02', '10:00:00', '11:00:00', TRUE, 'Boquilla instalada, prueba de presión exitosa'),
(2, 'OM-2026-005', '2026-07-11', NULL, '08:00:00', NULL, FALSE, 'En espera de técnico especializado'),
(4, 'OM-2026-005', '2026-07-11', NULL, '09:30:00', NULL, FALSE, 'Conexiones verificadas, pendiente software');

INSERT INTO HERRA_ORDEN (herramienta, orden_mantenimiento) VALUES
(1, 'OM-2026-001'),
(1, 'OM-2026-002'),
(2, 'OM-2026-002'),
(2, 'OM-2026-003'),
(1, 'OM-2026-004'),
(2, 'OM-2026-005'),
(3, 'OM-2026-005');

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- FIN DEL SCRIPT MAESTRO
-- =====================================================================