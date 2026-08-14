-- =====================================================================
-- OperaCore CMMS -- SCRIPT DE CARGA DE DATOS PARA DEMO (12-ago-2026)
-- Requiere: beta4.sql + triggers2.sql + sp.sql + vistas_kpi.sql YA
-- ejecutados y la BD 'operacore' con el seed original de beta4.sql
-- todavia presente (no borra nada, solo agrega).
--
-- Contenido:
--  1) Tercera linea de produccion (LI003, area ARR002) con 3 maquinas
--     nuevas (MAQ007-MAQ009) y su alta en TIPO_MAQUINA_AREA.
--  2) Piezas y REFACC_MAQUI para las maquinas nuevas.
--  3) ~28 reportes de falla historicos + sus ordenes correctivas ya
--     cerradas (INSERT con fechaCierre = NULL y luego UPDATE, para que
--     SI disparen tg_actualizar_mttr_orden) repartidos entre TODOS los
--     tecnicos.
--  4) 1 incidente abierto adicional (para ver el dashboard con algo
--     'en atencion' el dia de la demo).
--  5) 9 ordenes de mantenimiento PREVENTIVO ya programadas (una por
--     maquina) con fecha entre el 11 y el 26 de agosto 2026, con sus
--     tareas, herramientas y cuadrilla (incluye a TODOS los admins y
--     al encargado de linea como parte de la cuadrilla/supervision).
--  6) REGISTRO_OPS nuevos para todas las maquinas (dispara
--     tg_actualizar_mtbf_registroops).
--  7) Lecturas de sensor recientes (monitoreo) para las 9 maquinas.
--  8) HISTORIAL_ESTADO_MAQUINA para las maquinas que no estan 'OPERA'.
--  9) Historial "propio" (como trabajador principal, no solo cuadrilla)
--     para los 6 perfiles administrativos/encargado que en la version
--     anterior del script se quedaban sin actividad visible en su ficha
--     (NOM-002, NOM-004, NOM001, NOM-LDGR, NOM-SAU1, NOM-ALEX): 1 reporte
--     de falla + 1 orden correctiva ya cerrada + 1 orden preventiva
--     pendiente, cada uno. Ver seccion 9 abajo para el porque.
--
-- Uso: mysql -u <usuario> -p operacore < seed_demo.sql
--
-- >>> CAMBIOS vs version anterior (fix error #1451 al borrar LINEA):
-- La limpieza de MAQUINA/PIEZA/REFACC_MAQUI/HISTORIAL_ESTADO_MAQUINA
-- ahora se hace por RELACION (linea = 'LI003' / maquina en subquery)
-- en vez de por lista fija de codigos ('MAQ007','MAQ008','MAQ009').
-- Asi, si en una corrida anterior quedo alguna maquina de prueba
-- colgada de LI003 con OTRO codigo, este script la limpia igual y no
-- truena el DELETE FROM LINEA. Ver comentarios "FIX" abajo.
--
-- >>> CAMBIOS vs version anterior (seccion 9, NUEVA):
-- Se agrega historial propio para los perfiles que se veian "vacios"
-- en /mantenimiento/trabajadores/<numeroNomina>/. La vista
-- TrabajadorDetalleView (apps/mantenimiento/views.py del client) arma
-- los contadores de la ficha ("Ordenes asignadas", "Ordenes cerradas",
-- "Fallas reportadas", "Maquinas atendidas") consultando UNICAMENTE:
--   - ORDEN_MANTENIMIENTO.trabajador = <numeroNomina>   (responsable)
--   - REPORTE_FALLA.trabajador       = <numeroNomina>   (quien reporto)
-- NO cuenta a nadie que solo aparezca en TRABA_ORDE_PERSONAL (cuadrilla
-- de apoyo/supervision). Por eso, aunque la version anterior de este
-- script ya metia a los admins como cuadrilla en los 9 preventivos, sus
-- fichas seguian saliendo vacias: nunca eran el campo "trabajador" de
-- ninguna orden ni reporte. La seccion 9 corrige eso.
-- =====================================================================

SET NAMES utf8mb4;
USE operacore;
SET FOREIGN_KEY_CHECKS = 0;

-- =====================================================================
-- 0. LIMPIEZA (hace el script re-ejecutable). Borra UNICAMENTE lo que
--    este mismo script inserta, identificado por sus propios rangos
--    (folios OM-2026-006 en adelante, reportes de falla con id >= 6,
--    maquinas MAQ007-MAQ009, linea LI003, etc.). Si es la primera vez
--    que lo corres, todos estos DELETE simplemente no borran nada.
--    Los rangos ">= 'OM-2026-006'" y ">= 6" ya cubren tambien los
--    folios/reportes nuevos de la seccion 9 (043-054 / 34-39), asi que
--    no hizo falta tocar esta parte.
-- =====================================================================
DELETE FROM TRABA_ORDE_PERSONAL WHERE orden_mantenimiento >= 'OM-2026-006';
DELETE FROM TAREA_ORDEN         WHERE orden_mantenimiento >= 'OM-2026-006';
DELETE FROM HERRA_ORDEN         WHERE orden_mantenimiento >= 'OM-2026-006';
DELETE FROM MOVIMIENTO          WHERE orden_mantenimiento >= 'OM-2026-006';
DELETE FROM TIPO_REPORTE        WHERE reporte_falla >= 6;
DELETE FROM ORDEN_MANTENIMIENTO WHERE folio >= 'OM-2026-006';
DELETE FROM REPORTE_FALLA       WHERE numeroRegistro >= 6;
DELETE FROM REGISTRO_OPS        WHERE fechaInicio IN ('2026-02-01','2026-04-01','2026-07-01');
DELETE FROM LECTURA_SENSOR      WHERE (maquina IN ('MAQ001','MAQ002','MAQ003','MAQ004','MAQ005','MAQ006','MAQ007','MAQ008','MAQ009') AND `timestamp` >= '2026-08-09 00:00:00')
                                    OR maquina IN (SELECT codigo FROM MAQUINA WHERE linea = 'LI003'); -- FIX: cubre tambien maquinas de LI003 con otro codigo
DELETE FROM HISTORIAL_ESTADO_MAQUINA WHERE maquina IN ('MAQ003','MAQ006','MAQ008','MAQ009')
                                    OR maquina IN (SELECT codigo FROM MAQUINA WHERE linea = 'LI003'); -- FIX: idem
DELETE FROM INDICADOR           WHERE fechaFin IS NULL;
-- FIX: antes filtraba por lista fija de codigos ('MAQ007','MAQ008','MAQ009'), lo que
-- dejaba huerfanas las piezas/refacciones de cualquier maquina de LI003 con otro codigo
-- (por ejemplo si quedo una maquina de prueba de una corrida anterior). Ahora se limpia
-- por relacion a la linea, que es lo que realmente importa.
DELETE FROM REFACC_MAQUI        WHERE maquina IN (SELECT codigo FROM MAQUINA WHERE linea = 'LI003')
                                    OR (maquina='MAQ002' AND refaccion=4) OR (maquina='MAQ006' AND refaccion=5);
DELETE FROM PIEZA               WHERE maquina IN (SELECT codigo FROM MAQUINA WHERE linea = 'LI003')
                                    OR numeroSerie IN ('PS-YPK2-002','PS-HLR6-002','PS-VTS-002');
-- FIX PRINCIPAL (causa del error #1451): antes era
--   DELETE FROM MAQUINA WHERE codigo IN ('MAQ007','MAQ008','MAQ009');
-- que NO borraba una maquina que estuviera apuntando a LI003 con otro codigo.
-- Al borrar por relacion (linea = 'LI003') se garantiza que, cuando lleguemos
-- al DELETE FROM LINEA de mas abajo, ya no quede ninguna maquina hija.
DELETE FROM MAQUINA             WHERE linea = 'LI003';
DELETE FROM TIPO_MAQUINA_AREA   WHERE area = 'ARR002';
DELETE FROM LINEA               WHERE codigo = 'LI003';

-- =====================================================================
-- 1. TERCERA LINEA DE PRODUCCION (LI003, area ARR002)
-- =====================================================================
INSERT INTO LINEA (codigo, nombre, descripcion, area) VALUES
('LI003', 'Línea de Producción 3', 'Tercera línea de ensamble SMT, arranque 2023', 'ARR002');

-- Autoriza los mismos 3 tipos de maquina (Pick&Place, Horno, AOI) en la
-- nueva area ARR002 -- sin esto el trigger tg_validar_tipo_maquina_area_insert
-- rechazaria el INSERT de las maquinas de abajo.
INSERT INTO TIPO_MAQUINA_AREA (tipo_maquina, area) VALUES
(1, 'ARR002'),  -- Pick & Place
(2, 'ARR002'),  -- Horno Reflow
(3, 'ARR002');  -- AOI

INSERT INTO MAQUINA (codigo, numeroSerie, nombre, descripcion, imagen_url, modelo_3d, fechaInstalacion, linea, marca, modelo, estado_maquina, tipo_maquina, modo_monitoreo, umbral_vibracion) VALUES
('MAQ007', 'SN-YAM-YPK2-002', 'Pick & Place Línea 3', 'Máquina de alta velocidad para colocación de componentes SMT, línea 3', 'images/YamahaYS12.png', 'images/YamahaYS12.glb', '2023-05-10', 'LI003', 'YAMHA', 'YPK2', 'OPERA', 1, 'simulado', 4.0),
('MAQ008', 'SN-HEL-HLR6-002', 'Horno Reflow Línea 3', 'Horno de reflow con 6 zonas de temperatura, línea 3', 'images/Heller1707MK5.png', 'images/Heller1707MK5.glb', '2023-05-10', 'LI003', 'HELR', 'HLR6', 'FALLO', 2, 'simulado', 4.0),
('MAQ009', 'SN-OMR-VTS-002', 'AOI Línea 3', 'Sistema de inspección óptica automatizada 3D, línea 3', 'images/KohYoungZenithAlpha3D.png', 'images/KohYoungZenithAlpha3D.glb', '2023-08-22', 'LI003', 'OMRN', 'VT-S', 'MANTE', 3, 'simulado', 4.0);

-- Piezas de las 3 maquinas nuevas
INSERT INTO PIEZA (numeroSerie, codigoEtiqueta, nombre, costoInicial, horasOperacion, tiempoVidaUtil, depresacionAnual, valorResidual, fechaInstalacion, fechaGarantia, edo_pieza, maquina, tipo_pieza) VALUES
('PS-YPK2-002', 'ETQ-YPK2-002', 'Cabezal pickup línea 3', 132.00, 5200, 10000, 10.56, 25.00, '2023-05-10', '2025-05-10', 'OPERA', 'MAQ007', 1),
('PS-HLR6-002', 'ETQ-HLR6-002', 'Termopar zona 2 horno línea 3', 310.00, 9200, 15000, 18.90, 26.00, '2023-05-10', '2025-05-10', 'FALLI', 'MAQ008', 3),
('PS-VTS-002', 'ETQ-VTS-002', 'Cámara 3D principal línea 3', 4700.00, 4100, 20000, 215.00, 300.00, '2023-08-22', '2025-08-22', 'DEGRA', 'MAQ009', 3);

INSERT INTO REFACC_MAQUI (maquina, refaccion) VALUES
('MAQ007', 1), ('MAQ007', 2),
('MAQ008', 3),
('MAQ009', 3),
('MAQ002', 4), ('MAQ006', 5);

-- =====================================================================
-- 2. HISTORIAL: reportes de falla + ordenes correctivas (repartidos
--    entre TODOS los tecnicos). Las ordenes se insertan ABIERTAS y
--    se cierran con UPDATE aparte para que SI disparen
--    tg_actualizar_mttr_orden (igual pasa con tg_actualizar_mtbf_
--    registroops via REGISTRO_OPS mas abajo).
-- =====================================================================
INSERT INTO REPORTE_FALLA (numeroRegistro, asunto, fechaResolucion, fechaCreacion, horaCreacion, tiempoParo, causaRaiz, descripcion, imagen, maquina, trabajador, tipo_severidad, estado_reporte) VALUES
(6, 'Desalineación del cabezal por golpe de tope mecánico', DATE_ADD('2026-01-13', INTERVAL 2 DAY), '2026-01-13', '08:07:00', 3, 'El cabezal perdió referencia de origen tras un golpe, coloca - causa raiz confirmada en diagnostico', 'El cabezal perdió referencia de origen tras un golpe, colocación imprecisa de componentes 0402', NULL, 'MAQ001', 'NOM-001', 'ALTA', 'CERRA'),
(7, 'Falla intermitente en driver del motor del eje Y', DATE_ADD('2026-03-16', INTERVAL 3 DAY), '2026-03-16', '09:14:00', 4, 'El eje Y se detiene aleatoriamente durante el ciclo, se dete - causa raiz confirmada en diagnostico', 'El eje Y se detiene aleatoriamente durante el ciclo, se detectó driver con sobrecalentamiento', NULL, 'MAQ001', 'NOM-003', 'MEDIA', 'CERRA'),
(8, 'Nozzle obstruido por residuo de pasta', DATE_ADD('2026-05-19', INTERVAL 4 DAY), '2026-05-19', '10:21:00', 5, 'Pérdida de succión en nozzle #3, componentes caían durante e - causa raiz confirmada en diagnostico', 'Pérdida de succión en nozzle #3, componentes caían durante el traslado', NULL, 'MAQ001', 'NOM-XD1', 'BAJA', 'CERRA'),
(9, 'Termopar dañado en zona 4', DATE_ADD('2026-07-22', INTERVAL 1 DAY), '2026-07-22', '11:28:00', 6, 'Lectura errática de temperatura, riesgo de soldadura fría - causa raiz confirmada en diagnostico', 'Lectura errática de temperatura, riesgo de soldadura fría', NULL, 'MAQ002', 'NOM-GALL', 'ALTA', 'CERRA'),
(10, 'Ventilador de enfriamiento con rodamiento desgastado', DATE_ADD('2026-01-10', INTERVAL 2 DAY), '2026-01-10', '12:35:00', 7, 'Ruido excesivo y enfriamiento insuficiente en zona de salida - causa raiz confirmada en diagnostico', 'Ruido excesivo y enfriamiento insuficiente en zona de salida', NULL, 'MAQ002', 'NOM-SAU2', 'MEDIA', 'CERRA'),
(11, 'Cadena transportadora del horno desalineada', DATE_ADD('2026-03-13', INTERVAL 3 DAY), '2026-03-13', '13:42:00', 8, 'PCBs se atoran al pasar entre zonas 2 y 3 - causa raiz confirmada en diagnostico', 'PCBs se atoran al pasar entre zonas 2 y 3', NULL, 'MAQ002', 'NOM-ZUNI', 'MEDIA', 'CERRA'),
(12, 'Cámara principal pierde foco de manera intermitente', DATE_ADD('2026-05-16', INTERVAL 4 DAY), '2026-05-16', '14:49:00', 9, 'Falsos positivos y falsos negativos en la inspección - causa raiz confirmada en diagnostico', 'Falsos positivos y falsos negativos en la inspección', NULL, 'MAQ003', 'NOM-001', 'ALTA', 'CERRA'),
(13, 'Error en algoritmo de comparación de imágenes', DATE_ADD('2026-07-19', INTERVAL 1 DAY), '2026-07-19', '15:56:00', 10, 'El sistema rechaza PCBs correctamente ensambladas - causa raiz confirmada en diagnostico', 'El sistema rechaza PCBs correctamente ensambladas', NULL, 'MAQ003', 'NOM-003', 'MEDIA', 'CERRA'),
(14, 'Iluminación LED de anillo con degradación', DATE_ADD('2026-01-22', INTERVAL 2 DAY), '2026-01-22', '16:03:00', 11, 'Contraste insuficiente para detectar defectos de soldadura - causa raiz confirmada en diagnostico', 'Contraste insuficiente para detectar defectos de soldadura', NULL, 'MAQ003', 'NOM-XD1', 'BAJA', 'CERRA'),
(15, 'Boquilla dispensadora desgastada', DATE_ADD('2026-03-10', INTERVAL 3 DAY), '2026-03-10', '07:10:00', 12, 'Fuga de pasta de soldadura fuera del patrón de aplicación - causa raiz confirmada en diagnostico', 'Fuga de pasta de soldadura fuera del patrón de aplicación', NULL, 'MAQ004', 'NOM-GALL', 'MEDIA', 'CERRA'),
(16, 'Fuga en línea de presión de la jeringa', DATE_ADD('2026-05-13', INTERVAL 4 DAY), '2026-05-13', '08:17:00', 13, 'Volumen de pasta dispensada inconsistente - causa raiz confirmada en diagnostico', 'Volumen de pasta dispensada inconsistente', NULL, 'MAQ004', 'NOM-SAU2', 'ALTA', 'CERRA'),
(17, 'Sensor de nivel de pasta descalibrado', DATE_ADD('2026-07-16', INTERVAL 1 DAY), '2026-07-16', '09:24:00', 14, 'Alarma de nivel bajo aun con jeringa llena - causa raiz confirmada en diagnostico', 'Alarma de nivel bajo aun con jeringa llena', NULL, 'MAQ004', 'NOM-ZUNI', 'BAJA', 'CERRA'),
(18, 'Rodillo tensor de banda desgastado', DATE_ADD('2026-01-19', INTERVAL 2 DAY), '2026-01-19', '10:31:00', 15, 'Banda transportadora patina y detiene el flujo de PCBs - causa raiz confirmada en diagnostico', 'Banda transportadora patina y detiene el flujo de PCBs', NULL, 'MAQ005', 'NOM-001', 'MEDIA', 'CERRA'),
(19, 'Motor principal con consumo elevado', DATE_ADD('2026-03-22', INTERVAL 3 DAY), '2026-03-22', '11:38:00', 16, 'Sobrecalentamiento del motor tras 4 horas de operación conti - causa raiz confirmada en diagnostico', 'Sobrecalentamiento del motor tras 4 horas de operación continua', NULL, 'MAQ005', 'NOM-003', 'ALTA', 'CERRA'),
(20, 'Sensor de fin de carrera desalineado', DATE_ADD('2026-05-10', INTERVAL 4 DAY), '2026-05-10', '12:45:00', 17, 'PCBs se detienen antes de la posición de entrega - causa raiz confirmada en diagnostico', 'PCBs se detienen antes de la posición de entrega', NULL, 'MAQ005', 'NOM-XD1', 'BAJA', 'CERRA'),
(21, 'Congelamiento intermitente de interfaz de prueba', DATE_ADD('2026-07-13', INTERVAL 1 DAY), '2026-07-13', '13:52:00', 18, 'La estación deja de responder a mitad de la secuencia de pru - causa raiz confirmada en diagnostico', 'La estación deja de responder a mitad de la secuencia de prueba', NULL, 'MAQ006', 'NOM-GALL', 'CRITI', 'CERRA'),
(22, 'Sonda de prueba con contacto defectuoso', DATE_ADD('2026-01-16', INTERVAL 2 DAY), '2026-01-16', '14:59:00', 19, 'Falsos rechazos en canal 3 de prueba - causa raiz confirmada en diagnostico', 'Falsos rechazos en canal 3 de prueba', NULL, 'MAQ006', 'NOM-SAU2', 'MEDIA', 'CERRA'),
(23, 'Desfase en calibración multicanal', DATE_ADD('2026-03-19', INTERVAL 3 DAY), '2026-03-19', '15:06:00', 20, 'Resultados de prueba inconsistentes entre corridas - causa raiz confirmada en diagnostico', 'Resultados de prueba inconsistentes entre corridas', NULL, 'MAQ006', 'NOM-ZUNI', 'ALTA', 'CERRA'),
(24, 'Desgaste en correa de eje X', DATE_ADD('2026-05-22', INTERVAL 4 DAY), '2026-05-22', '16:13:00', 21, 'Vibración anormal en el desplazamiento del eje X, correa con - causa raiz confirmada en diagnostico', 'Vibración anormal en el desplazamiento del eje X, correa con grietas visibles', NULL, 'MAQ007', 'NOM-001', 'MEDIA', 'CERRA'),
(25, 'Sensor de reconocimiento de componentes desalineado', DATE_ADD('2026-07-10', INTERVAL 1 DAY), '2026-07-10', '07:20:00', 2, 'El sistema de visión no reconoce componentes pequeños, recha - causa raiz confirmada en diagnostico', 'El sistema de visión no reconoce componentes pequeños, rechazo elevado', NULL, 'MAQ007', 'NOM-003', 'ALTA', 'CERRA'),
(26, 'Nozzle #2 con fuga de vacío', DATE_ADD('2026-01-13', INTERVAL 2 DAY), '2026-01-13', '08:27:00', 3, 'Componentes caen antes de llegar al punto de colocación - causa raiz confirmada en diagnostico', 'Componentes caen antes de llegar al punto de colocación', NULL, 'MAQ007', 'NOM-XD1', 'BAJA', 'CERRA'),
(27, 'Resistencia de zona 2 con falla parcial', DATE_ADD('2026-03-16', INTERVAL 3 DAY), '2026-03-16', '09:34:00', 4, 'Perfil térmico no alcanza set point, retrabajo elevado - causa raiz confirmada en diagnostico', 'Perfil térmico no alcanza set point, retrabajo elevado', NULL, 'MAQ008', 'NOM-GALL', 'ALTA', 'CERRA'),
(28, 'Banda de arrastre patina en zona de entrada', DATE_ADD('2026-05-19', INTERVAL 4 DAY), '2026-05-19', '10:41:00', 5, 'PCBs entran desalineados al horno - causa raiz confirmada en diagnostico', 'PCBs entran desalineados al horno', NULL, 'MAQ008', 'NOM-SAU2', 'BAJA', 'CERRA'),
(29, 'Falla en tarjeta de control de temperatura', DATE_ADD('2026-07-22', INTERVAL 1 DAY), '2026-07-22', '11:48:00', 6, 'Horno no responde a cambios de perfil térmico - causa raiz confirmada en diagnostico', 'Horno no responde a cambios de perfil térmico', NULL, 'MAQ008', 'NOM-ZUNI', 'CRITI', 'CERRA'),
(30, 'Falla en el sistema de doble cámara 3D', DATE_ADD('2026-01-10', INTERVAL 2 DAY), '2026-01-10', '12:55:00', 7, 'Medición de altura de componentes fuera de tolerancia - causa raiz confirmada en diagnostico', 'Medición de altura de componentes fuera de tolerancia', NULL, 'MAQ009', 'NOM-001', 'ALTA', 'CERRA'),
(31, 'Calibración de patrón perdida tras actualización', DATE_ADD('2026-03-13', INTERVAL 3 DAY), '2026-03-13', '13:02:00', 8, 'Rechazo masivo de PCBs sin defecto real - causa raiz confirmada en diagnostico', 'Rechazo masivo de PCBs sin defecto real', NULL, 'MAQ009', 'NOM-003', 'MEDIA', 'CERRA'),
(32, 'Fuente de iluminación estroboscópica intermitente', DATE_ADD('2026-05-16', INTERVAL 4 DAY), '2026-05-16', '14:09:00', 9, 'Imágenes borrosas en inspección a alta velocidad - causa raiz confirmada en diagnostico', 'Imágenes borrosas en inspección a alta velocidad', NULL, 'MAQ009', 'NOM-XD1', 'MEDIA', 'CERRA');

INSERT INTO TIPO_REPORTE (tipo_falla, reporte_falla) VALUES
(1, 6),
(2, 7),
(1, 8),
(2, 9),
(1, 10),
(1, 11),
(5, 12),
(4, 13),
(5, 14),
(1, 15),
(3, 16),
(2, 17),
(1, 18),
(2, 19),
(1, 20),
(4, 21),
(2, 22),
(4, 23),
(1, 24),
(5, 25),
(1, 26),
(2, 27),
(1, 28),
(2, 29),
(5, 30),
(4, 31),
(2, 32);

-- Ordenes se insertan ABIERTAS (fechaCierre NULL) a proposito:
INSERT INTO ORDEN_MANTENIMIENTO (folio, descripcion, diagnostico, notas, fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre, horasIntervenidas, porcentaje, imagen, maquina, trabajador, reporte_falla, tipo_mantenimiento, estado_orden) VALUES
('OM-2026-006', 'Atención correctiva: desalineación del cabezal por golpe de tope mecánico', 'El cabezal perdió referencia de origen tras un golpe, colocación imprecisa de componentes 0402', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-01-13', '2026-01-13', '08:07:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ001', 'NOM-001', 6, 'CORRE', 'ENPRO'),
('OM-2026-007', 'Atención correctiva: falla intermitente en driver del motor del eje y', 'El eje Y se detiene aleatoriamente durante el ciclo, se detectó driver con sobrecalentamiento', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-16', '2026-03-16', '09:14:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ001', 'NOM-003', 7, 'CORRE', 'ENPRO'),
('OM-2026-008', 'Atención correctiva: nozzle obstruido por residuo de pasta', 'Pérdida de succión en nozzle #3, componentes caían durante el traslado', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-05-19', '2026-05-19', '10:21:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ001', 'NOM-XD1', 8, 'CORRE', 'ENPRO'),
('OM-2026-009', 'Atención correctiva: termopar dañado en zona 4', 'Lectura errática de temperatura, riesgo de soldadura fría', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-07-22', '2026-07-22', '11:28:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ002', 'NOM-GALL', 9, 'CORRE', 'ENPRO'),
('OM-2026-010', 'Atención correctiva: ventilador de enfriamiento con rodamiento desgastado', 'Ruido excesivo y enfriamiento insuficiente en zona de salida', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-01-10', '2026-01-10', '12:35:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ002', 'NOM-SAU2', 10, 'CORRE', 'ENPRO'),
('OM-2026-011', 'Atención correctiva: cadena transportadora del horno desalineada', 'PCBs se atoran al pasar entre zonas 2 y 3', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-13', '2026-03-13', '13:42:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ002', 'NOM-ZUNI', 11, 'CORRE', 'ENPRO'),
('OM-2026-012', 'Atención correctiva: cámara principal pierde foco de manera intermitente', 'Falsos positivos y falsos negativos en la inspección', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-05-16', '2026-05-16', '14:49:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ003', 'NOM-001', 12, 'CORRE', 'ENPRO'),
('OM-2026-013', 'Atención correctiva: error en algoritmo de comparación de imágenes', 'El sistema rechaza PCBs correctamente ensambladas', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-07-19', '2026-07-19', '15:56:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ003', 'NOM-003', 13, 'CORRE', 'ENPRO'),
('OM-2026-014', 'Atención correctiva: iluminación led de anillo con degradación', 'Contraste insuficiente para detectar defectos de soldadura', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-01-22', '2026-01-22', '16:03:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ003', 'NOM-XD1', 14, 'CORRE', 'ENPRO'),
('OM-2026-015', 'Atención correctiva: boquilla dispensadora desgastada', 'Fuga de pasta de soldadura fuera del patrón de aplicación', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-10', '2026-03-10', '07:10:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ004', 'NOM-GALL', 15, 'CORRE', 'ENPRO'),
('OM-2026-016', 'Atención correctiva: fuga en línea de presión de la jeringa', 'Volumen de pasta dispensada inconsistente', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-05-13', '2026-05-13', '08:17:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ004', 'NOM-SAU2', 16, 'CORRE', 'ENPRO'),
('OM-2026-017', 'Atención correctiva: sensor de nivel de pasta descalibrado', 'Alarma de nivel bajo aun con jeringa llena', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-07-16', '2026-07-16', '09:24:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ004', 'NOM-ZUNI', 17, 'CORRE', 'ENPRO'),
('OM-2026-018', 'Atención correctiva: rodillo tensor de banda desgastado', 'Banda transportadora patina y detiene el flujo de PCBs', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-01-19', '2026-01-19', '10:31:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ005', 'NOM-001', 18, 'CORRE', 'ENPRO'),
('OM-2026-019', 'Atención correctiva: motor principal con consumo elevado', 'Sobrecalentamiento del motor tras 4 horas de operación continua', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-22', '2026-03-22', '11:38:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ005', 'NOM-003', 19, 'CORRE', 'ENPRO'),
('OM-2026-020', 'Atención correctiva: sensor de fin de carrera desalineado', 'PCBs se detienen antes de la posición de entrega', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-05-10', '2026-05-10', '12:45:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ005', 'NOM-XD1', 20, 'CORRE', 'ENPRO'),
('OM-2026-021', 'Atención correctiva: congelamiento intermitente de interfaz de prueba', 'La estación deja de responder a mitad de la secuencia de prueba', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-07-13', '2026-07-13', '13:52:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ006', 'NOM-GALL', 21, 'CORRE', 'ENPRO'),
('OM-2026-022', 'Atención correctiva: sonda de prueba con contacto defectuoso', 'Falsos rechazos en canal 3 de prueba', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-01-16', '2026-01-16', '14:59:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ006', 'NOM-SAU2', 22, 'CORRE', 'ENPRO'),
('OM-2026-023', 'Atención correctiva: desfase en calibración multicanal', 'Resultados de prueba inconsistentes entre corridas', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-19', '2026-03-19', '15:06:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ006', 'NOM-ZUNI', 23, 'CORRE', 'ENPRO'),
('OM-2026-024', 'Atención correctiva: desgaste en correa de eje x', 'Vibración anormal en el desplazamiento del eje X, correa con grietas visibles', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-05-22', '2026-05-22', '16:13:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ007', 'NOM-001', 24, 'CORRE', 'ENPRO'),
('OM-2026-025', 'Atención correctiva: sensor de reconocimiento de componentes desalineado', 'El sistema de visión no reconoce componentes pequeños, rechazo elevado', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-07-10', '2026-07-10', '07:20:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ007', 'NOM-003', 25, 'CORRE', 'ENPRO'),
('OM-2026-026', 'Atención correctiva: nozzle #2 con fuga de vacío', 'Componentes caen antes de llegar al punto de colocación', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-01-13', '2026-01-13', '08:27:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ007', 'NOM-XD1', 26, 'CORRE', 'ENPRO'),
('OM-2026-027', 'Atención correctiva: resistencia de zona 2 con falla parcial', 'Perfil térmico no alcanza set point, retrabajo elevado', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-16', '2026-03-16', '09:34:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ008', 'NOM-GALL', 27, 'CORRE', 'ENPRO'),
('OM-2026-028', 'Atención correctiva: banda de arrastre patina en zona de entrada', 'PCBs entran desalineados al horno', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-05-19', '2026-05-19', '10:41:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ008', 'NOM-SAU2', 28, 'CORRE', 'ENPRO'),
('OM-2026-029', 'Atención correctiva: falla en tarjeta de control de temperatura', 'Horno no responde a cambios de perfil térmico', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-07-22', '2026-07-22', '11:48:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ008', 'NOM-ZUNI', 29, 'CORRE', 'ENPRO'),
('OM-2026-030', 'Atención correctiva: falla en el sistema de doble cámara 3d', 'Medición de altura de componentes fuera de tolerancia', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-01-10', '2026-01-10', '12:55:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ009', 'NOM-001', 30, 'CORRE', 'ENPRO'),
('OM-2026-031', 'Atención correctiva: calibración de patrón perdida tras actualización', 'Rechazo masivo de PCBs sin defecto real', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-13', '2026-03-13', '13:02:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ009', 'NOM-003', 31, 'CORRE', 'ENPRO'),
('OM-2026-032', 'Atención correctiva: fuente de iluminación estroboscópica intermitente', 'Imágenes borrosas en inspección a alta velocidad', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-05-16', '2026-05-16', '14:09:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ009', 'NOM-XD1', 32, 'CORRE', 'ENPRO');

-- Se cierran una por una: cada UPDATE dispara tg_actualizar_mttr_orden
-- (OLD.fechaCierre IS NULL AND NEW.fechaCierre IS NOT NULL), que recalcula
-- el MTTR de esa maquina y actualiza/crea su periodo vigente en INDICADOR.
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-01-13', INTERVAL 2 DAY), horaCierre = '10:11:00', horasIntervenidas = 2.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-006';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-16', INTERVAL 3 DAY), horaCierre = '11:22:00', horasIntervenidas = 3.0, estado_orden = 'CERRA' WHERE folio = 'OM-2026-007';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-05-19', INTERVAL 4 DAY), horaCierre = '12:33:00', horasIntervenidas = 3.75, estado_orden = 'CERRA' WHERE folio = 'OM-2026-008';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-07-22', INTERVAL 1 DAY), horaCierre = '13:44:00', horasIntervenidas = 4.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-009';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-01-10', INTERVAL 2 DAY), horaCierre = '14:55:00', horasIntervenidas = 5.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-010';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-13', INTERVAL 3 DAY), horaCierre = '15:06:00', horasIntervenidas = 1.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-011';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-05-16', INTERVAL 4 DAY), horaCierre = '16:17:00', horasIntervenidas = 2.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-012';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-07-19', INTERVAL 1 DAY), horaCierre = '09:28:00', horasIntervenidas = 3.0, estado_orden = 'CERRA' WHERE folio = 'OM-2026-013';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-01-22', INTERVAL 2 DAY), horaCierre = '10:39:00', horasIntervenidas = 3.75, estado_orden = 'CERRA' WHERE folio = 'OM-2026-014';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-10', INTERVAL 3 DAY), horaCierre = '11:50:00', horasIntervenidas = 4.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-015';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-05-13', INTERVAL 4 DAY), horaCierre = '12:01:00', horasIntervenidas = 5.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-016';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-07-16', INTERVAL 1 DAY), horaCierre = '13:12:00', horasIntervenidas = 1.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-017';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-01-19', INTERVAL 2 DAY), horaCierre = '14:23:00', horasIntervenidas = 2.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-018';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-22', INTERVAL 3 DAY), horaCierre = '15:34:00', horasIntervenidas = 3.0, estado_orden = 'CERRA' WHERE folio = 'OM-2026-019';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-05-10', INTERVAL 4 DAY), horaCierre = '16:45:00', horasIntervenidas = 3.75, estado_orden = 'CERRA' WHERE folio = 'OM-2026-020';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-07-13', INTERVAL 1 DAY), horaCierre = '09:56:00', horasIntervenidas = 4.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-021';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-01-16', INTERVAL 2 DAY), horaCierre = '10:07:00', horasIntervenidas = 5.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-022';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-19', INTERVAL 3 DAY), horaCierre = '11:18:00', horasIntervenidas = 1.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-023';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-05-22', INTERVAL 4 DAY), horaCierre = '12:29:00', horasIntervenidas = 2.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-024';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-07-10', INTERVAL 1 DAY), horaCierre = '13:40:00', horasIntervenidas = 3.0, estado_orden = 'CERRA' WHERE folio = 'OM-2026-025';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-01-13', INTERVAL 2 DAY), horaCierre = '14:51:00', horasIntervenidas = 3.75, estado_orden = 'CERRA' WHERE folio = 'OM-2026-026';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-16', INTERVAL 3 DAY), horaCierre = '15:02:00', horasIntervenidas = 4.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-027';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-05-19', INTERVAL 4 DAY), horaCierre = '16:13:00', horasIntervenidas = 5.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-028';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-07-22', INTERVAL 1 DAY), horaCierre = '09:24:00', horasIntervenidas = 1.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-029';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-01-10', INTERVAL 2 DAY), horaCierre = '10:35:00', horasIntervenidas = 2.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-030';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-13', INTERVAL 3 DAY), horaCierre = '11:46:00', horasIntervenidas = 3.0, estado_orden = 'CERRA' WHERE folio = 'OM-2026-031';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-05-16', INTERVAL 4 DAY), horaCierre = '12:57:00', horasIntervenidas = 3.75, estado_orden = 'CERRA' WHERE folio = 'OM-2026-032';

INSERT INTO TAREA_ORDEN (tarea, orden_mantenimiento, fechaInicio, fechaCierre, horaInicio, horafin, verificacion, observaciones) VALUES
(2, 'OM-2026-006', '2026-01-13', DATE_ADD('2026-01-13', INTERVAL 2 DAY), '08:07:00', '10:11:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(3, 'OM-2026-007', '2026-03-16', DATE_ADD('2026-03-16', INTERVAL 3 DAY), '09:14:00', '11:22:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(4, 'OM-2026-008', '2026-05-19', DATE_ADD('2026-05-19', INTERVAL 4 DAY), '10:21:00', '12:33:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(5, 'OM-2026-009', '2026-07-22', DATE_ADD('2026-07-22', INTERVAL 1 DAY), '11:28:00', '13:44:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(1, 'OM-2026-010', '2026-01-10', DATE_ADD('2026-01-10', INTERVAL 2 DAY), '12:35:00', '14:55:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(2, 'OM-2026-011', '2026-03-13', DATE_ADD('2026-03-13', INTERVAL 3 DAY), '13:42:00', '15:06:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(3, 'OM-2026-012', '2026-05-16', DATE_ADD('2026-05-16', INTERVAL 4 DAY), '14:49:00', '16:17:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(4, 'OM-2026-013', '2026-07-19', DATE_ADD('2026-07-19', INTERVAL 1 DAY), '15:56:00', '09:28:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(5, 'OM-2026-014', '2026-01-22', DATE_ADD('2026-01-22', INTERVAL 2 DAY), '16:03:00', '10:39:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(1, 'OM-2026-015', '2026-03-10', DATE_ADD('2026-03-10', INTERVAL 3 DAY), '07:10:00', '11:50:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(2, 'OM-2026-016', '2026-05-13', DATE_ADD('2026-05-13', INTERVAL 4 DAY), '08:17:00', '12:01:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(3, 'OM-2026-017', '2026-07-16', DATE_ADD('2026-07-16', INTERVAL 1 DAY), '09:24:00', '13:12:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(4, 'OM-2026-018', '2026-01-19', DATE_ADD('2026-01-19', INTERVAL 2 DAY), '10:31:00', '14:23:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(5, 'OM-2026-019', '2026-03-22', DATE_ADD('2026-03-22', INTERVAL 3 DAY), '11:38:00', '15:34:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(1, 'OM-2026-020', '2026-05-10', DATE_ADD('2026-05-10', INTERVAL 4 DAY), '12:45:00', '16:45:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(2, 'OM-2026-021', '2026-07-13', DATE_ADD('2026-07-13', INTERVAL 1 DAY), '13:52:00', '09:56:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(3, 'OM-2026-022', '2026-01-16', DATE_ADD('2026-01-16', INTERVAL 2 DAY), '14:59:00', '10:07:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(4, 'OM-2026-023', '2026-03-19', DATE_ADD('2026-03-19', INTERVAL 3 DAY), '15:06:00', '11:18:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(5, 'OM-2026-024', '2026-05-22', DATE_ADD('2026-05-22', INTERVAL 4 DAY), '16:13:00', '12:29:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(1, 'OM-2026-025', '2026-07-10', DATE_ADD('2026-07-10', INTERVAL 1 DAY), '07:20:00', '13:40:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(2, 'OM-2026-026', '2026-01-13', DATE_ADD('2026-01-13', INTERVAL 2 DAY), '08:27:00', '14:51:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(3, 'OM-2026-027', '2026-03-16', DATE_ADD('2026-03-16', INTERVAL 3 DAY), '09:34:00', '15:02:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(4, 'OM-2026-028', '2026-05-19', DATE_ADD('2026-05-19', INTERVAL 4 DAY), '10:41:00', '16:13:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(5, 'OM-2026-029', '2026-07-22', DATE_ADD('2026-07-22', INTERVAL 1 DAY), '11:48:00', '09:24:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(1, 'OM-2026-030', '2026-01-10', DATE_ADD('2026-01-10', INTERVAL 2 DAY), '12:55:00', '10:35:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(2, 'OM-2026-031', '2026-03-13', DATE_ADD('2026-03-13', INTERVAL 3 DAY), '13:02:00', '11:46:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(3, 'OM-2026-032', '2026-05-16', DATE_ADD('2026-05-16', INTERVAL 4 DAY), '14:09:00', '12:57:00', TRUE, 'Verificado y documentado, sin observaciones pendientes');

INSERT INTO HERRA_ORDEN (herramienta, orden_mantenimiento) VALUES
(2, 'OM-2026-006'),
(3, 'OM-2026-007'),
(1, 'OM-2026-008'),
(2, 'OM-2026-009'),
(3, 'OM-2026-010'),
(1, 'OM-2026-011'),
(2, 'OM-2026-012'),
(3, 'OM-2026-013'),
(1, 'OM-2026-014'),
(2, 'OM-2026-015'),
(3, 'OM-2026-016'),
(1, 'OM-2026-017'),
(2, 'OM-2026-018'),
(3, 'OM-2026-019'),
(1, 'OM-2026-020'),
(2, 'OM-2026-021'),
(3, 'OM-2026-022'),
(1, 'OM-2026-023'),
(2, 'OM-2026-024'),
(3, 'OM-2026-025'),
(1, 'OM-2026-026'),
(2, 'OM-2026-027'),
(3, 'OM-2026-028'),
(1, 'OM-2026-029'),
(2, 'OM-2026-030'),
(3, 'OM-2026-031'),
(1, 'OM-2026-032');

INSERT INTO TRABA_ORDE_PERSONAL (trabajador, orden_mantenimiento) VALUES
('NOM-001', 'OM-2026-006'),
('NOM-003', 'OM-2026-007'),
('NOM-XD1', 'OM-2026-008'),
('NOM-GALL', 'OM-2026-009'),
('NOM-SAU2', 'OM-2026-010'),
('NOM-ZUNI', 'OM-2026-011'),
('NOM-001', 'OM-2026-012'),
('NOM-003', 'OM-2026-013'),
('NOM-XD1', 'OM-2026-014'),
('NOM-GALL', 'OM-2026-015'),
('NOM-SAU2', 'OM-2026-016'),
('NOM-ZUNI', 'OM-2026-017'),
('NOM-001', 'OM-2026-018'),
('NOM-003', 'OM-2026-019'),
('NOM-XD1', 'OM-2026-020'),
('NOM-GALL', 'OM-2026-021'),
('NOM-SAU2', 'OM-2026-022'),
('NOM-ZUNI', 'OM-2026-023'),
('NOM-001', 'OM-2026-024'),
('NOM-003', 'OM-2026-025'),
('NOM-XD1', 'OM-2026-026'),
('NOM-GALL', 'OM-2026-027'),
('NOM-SAU2', 'OM-2026-028'),
('NOM-ZUNI', 'OM-2026-029'),
('NOM-001', 'OM-2026-030'),
('NOM-003', 'OM-2026-031'),
('NOM-XD1', 'OM-2026-032');

-- =====================================================================
-- 3. INCIDENTE ABIERTO (para que el dashboard muestre algo 'en progreso'
--    el dia de la demo, ademas del que ya trae MAQ006 del seed original)
-- =====================================================================
INSERT INTO REPORTE_FALLA (numeroRegistro, asunto, fechaResolucion, fechaCreacion, horaCreacion, tiempoParo, causaRaiz, descripcion, imagen, maquina, trabajador, tipo_severidad, estado_reporte) VALUES
(33, 'Resistencia de zona 2 con falla parcial', NULL, '2026-08-09', '15:40:00', NULL, 'Resistencia de la zona 2 del horno con degradación, en diagnóstico por técnico', 'El horno no alcanza el set point en zona 2, se detectó durante monitoreo de rutina. Se detuvo la línea por precaución.', NULL, 'MAQ008', 'NOM-SAU2', 'CRITI', 'ENATE');
INSERT INTO TIPO_REPORTE (tipo_falla, reporte_falla) VALUES (2, 33);
INSERT INTO ORDEN_MANTENIMIENTO (folio, descripcion, diagnostico, notas, fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre, horasIntervenidas, porcentaje, imagen, maquina, trabajador, reporte_falla, tipo_mantenimiento, estado_orden) VALUES
('OM-2026-033', 'Diagnóstico y reparación de resistencia zona 2', 'En espera de refacción (resistencia de repuesto) para confirmar diagnóstico', 'Máquina detenida, se está evaluando con el proveedor tiempo de entrega de la refacción', NULL, '2026-08-09', '16:10:00', NULL, NULL, NULL, 35.00, NULL, 'MAQ008', 'NOM-SAU2', 33, 'CORRE', 'ENPRO');
INSERT INTO TRABA_ORDE_PERSONAL (trabajador, orden_mantenimiento) VALUES ('NOM-SAU2', 'OM-2026-033'), ('NOM-ALEX', 'OM-2026-033');
INSERT INTO TAREA_ORDEN (tarea, orden_mantenimiento, fechaInicio, fechaCierre, horaInicio, horafin, verificacion, observaciones) VALUES
(4, 'OM-2026-033', '2026-08-09', NULL, '16:15:00', NULL, FALSE, 'Conexiones eléctricas revisadas, pendiente refacción para continuar');

-- =====================================================================
-- 4. MANTENIMIENTOS PREVENTIVOS YA PROGRAMADOS (uno por maquina, 9 en
--    total), con fecha entre el 11 y el 26 de agosto 2026 -- listos
--    para mostrarse en el modulo de mantenimiento el dia de la demo.
--    Cuadrilla (TRABA_ORDE_PERSONAL) incluye tecnico + admin/enc. de
--    linea como supervision, para que TODOS los usuarios tengan
--    historial, incluidos los que no hacen reparaciones directas.
-- =====================================================================
INSERT INTO ORDEN_MANTENIMIENTO (folio, descripcion, diagnostico, notas, fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre, horasIntervenidas, porcentaje, imagen, maquina, trabajador, reporte_falla, tipo_mantenimiento, estado_orden) VALUES
('OM-2026-034', 'Mantenimiento preventivo trimestral: lubricación de ejes, calibración de cabezal y limpieza de nozzles', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-11', '2026-08-05', '09:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ001', 'NOM-GALL', NULL, 'PREVE', 'PROGR'),
('OM-2026-035', 'Mantenimiento preventivo: verificación de las 6 zonas de temperatura y limpieza de cadena transportadora', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-12', '2026-08-05', '10:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ002', 'NOM-SAU2', NULL, 'PREVE', 'APROB'),
('OM-2026-036', 'Mantenimiento preventivo: limpieza de lente, calibración de iluminación y verificación de software', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-13', '2026-08-05', '11:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ003', 'NOM-ZUNI', NULL, 'PREVE', 'SOLIC'),
('OM-2026-037', 'Mantenimiento preventivo: limpieza de boquilla, verificación de presión neumática y calibración de volumen', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-14', '2026-08-05', '12:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ004', 'NOM-001', NULL, 'PREVE', 'PROGR'),
('OM-2026-038', 'Mantenimiento preventivo: tensado de banda, lubricación de rodillos y verificación de sensores de posición', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-18', '2026-08-05', '13:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ005', 'NOM-003', NULL, 'PREVE', 'APROB'),
('OM-2026-039', 'Mantenimiento preventivo: calibración multicanal y verificación de sondas de prueba', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-19', '2026-08-05', '14:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ006', 'NOM-XD1', NULL, 'PREVE', 'PROGR'),
('OM-2026-040', 'Mantenimiento preventivo trimestral: lubricación de ejes, calibración de cabezal y limpieza de nozzles (línea 3)', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-20', '2026-08-05', '15:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ007', 'NOM-GALL', NULL, 'PREVE', 'SOLIC'),
('OM-2026-041', 'Mantenimiento preventivo: verificación de zonas de temperatura y calibración de sensores (línea 3)', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-25', '2026-08-05', '16:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ008', 'NOM-SAU2', NULL, 'PREVE', 'APROB'),
('OM-2026-042', 'Mantenimiento preventivo: limpieza de cámaras 3D y recalibración de patrón de referencia (línea 3)', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-26', '2026-08-05', '17:00:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ009', 'NOM-ZUNI', NULL, 'PREVE', 'PROGR');

INSERT INTO TAREA_ORDEN (tarea, orden_mantenimiento, fechaInicio, fechaCierre, horaInicio, horafin, verificacion, observaciones) VALUES
(1, 'OM-2026-034', '2026-08-11', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-11'),
(2, 'OM-2026-035', '2026-08-12', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-12'),
(3, 'OM-2026-036', '2026-08-13', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-13'),
(4, 'OM-2026-037', '2026-08-14', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-14'),
(5, 'OM-2026-038', '2026-08-18', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-18'),
(1, 'OM-2026-039', '2026-08-19', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-19'),
(2, 'OM-2026-040', '2026-08-20', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-20'),
(3, 'OM-2026-041', '2026-08-25', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-25'),
(4, 'OM-2026-042', '2026-08-26', NULL, '09:00:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-26');

INSERT INTO HERRA_ORDEN (herramienta, orden_mantenimiento) VALUES
(1, 'OM-2026-034'),
(2, 'OM-2026-035'),
(3, 'OM-2026-036'),
(1, 'OM-2026-037'),
(2, 'OM-2026-038'),
(3, 'OM-2026-039'),
(1, 'OM-2026-040'),
(2, 'OM-2026-041'),
(3, 'OM-2026-042');

INSERT INTO TRABA_ORDE_PERSONAL (trabajador, orden_mantenimiento) VALUES
('NOM-GALL', 'OM-2026-034'),
('NOM-004', 'OM-2026-034'),
('NOM-SAU2', 'OM-2026-035'),
('NOM001', 'OM-2026-035'),
('NOM-ZUNI', 'OM-2026-036'),
('NOM-LDGR', 'OM-2026-036'),
('NOM-001', 'OM-2026-037'),
('NOM-SAU1', 'OM-2026-037'),
('NOM-003', 'OM-2026-038'),
('NOM-ALEX', 'OM-2026-038'),
('NOM-XD1', 'OM-2026-039'),
('NOM-002', 'OM-2026-039'),
('NOM-GALL', 'OM-2026-040'),
('NOM-004', 'OM-2026-040'),
('NOM-SAU2', 'OM-2026-041'),
('NOM001', 'OM-2026-041'),
('NOM-ZUNI', 'OM-2026-042'),
('NOM-LDGR', 'OM-2026-042');

-- =====================================================================
-- 5. REGISTRO_OPS -- horas de operacion adicionales para TODAS las
--    maquinas (incluye las 3 nuevas). Cada INSERT dispara
--    tg_actualizar_mtbf_registroops, que recalcula el MTBF y crea/
--    actualiza el periodo vigente en INDICADOR automaticamente.
-- =====================================================================
INSERT INTO REGISTRO_OPS (fechaInicio, fechaFin, horasOperacion, maquina) VALUES
('2026-02-01', '2026-02-28', 205, 'MAQ001'),
('2026-04-01', '2026-04-30', 198, 'MAQ001'),
('2026-07-01', '2026-07-31', 191, 'MAQ001'),
('2026-02-01', '2026-02-28', 198, 'MAQ002'),
('2026-04-01', '2026-04-30', 191, 'MAQ002'),
('2026-07-01', '2026-07-31', 184, 'MAQ002'),
('2026-02-01', '2026-02-28', 150, 'MAQ003'),
('2026-04-01', '2026-04-30', 143, 'MAQ003'),
('2026-07-01', '2026-07-31', 136, 'MAQ003'),
('2026-02-01', '2026-02-28', 197, 'MAQ004'),
('2026-04-01', '2026-04-30', 190, 'MAQ004'),
('2026-07-01', '2026-07-31', 183, 'MAQ004'),
('2026-02-01', '2026-02-28', 208, 'MAQ005'),
('2026-04-01', '2026-04-30', 201, 'MAQ005'),
('2026-07-01', '2026-07-31', 194, 'MAQ005'),
('2026-02-01', '2026-02-28', 140, 'MAQ006'),
('2026-04-01', '2026-04-30', 133, 'MAQ006'),
('2026-07-01', '2026-07-31', 126, 'MAQ006'),
('2026-02-01', '2026-02-28', 180, 'MAQ007'),
('2026-04-01', '2026-04-30', 173, 'MAQ007'),
('2026-07-01', '2026-07-31', 166, 'MAQ007'),
('2026-02-01', '2026-02-28', 120, 'MAQ008'),
('2026-04-01', '2026-04-30', 113, 'MAQ008'),
('2026-07-01', '2026-07-31', 106, 'MAQ008'),
('2026-02-01', '2026-02-28', 160, 'MAQ009'),
('2026-04-01', '2026-04-30', 153, 'MAQ009'),
('2026-07-01', '2026-07-31', 146, 'MAQ009');

-- =====================================================================
-- 6. LECTURA_SENSOR -- lecturas recientes (9 y 10 de agosto 2026) para
--    todas las maquinas, para que el modulo de monitoreo tenga datos
--    frescos el dia de la demo. MAQ008 y MAQ009 incluyen lecturas que
--    EXCEDEN el umbral de vibracion, coherente con su estado actual.
-- =====================================================================
INSERT INTO LECTURA_SENSOR (maquina, `timestamp`, origen, vibracion, golpe, temperatura) VALUES
('MAQ001', '2026-08-09 08:00:00', 'simulado', 1.2, FALSE, 38.0),
('MAQ001', '2026-08-09 16:00:00', 'simulado', 1.35, FALSE, 38.6),
('MAQ001', '2026-08-10 08:00:00', 'simulado', 1.5, FALSE, 39.2),
('MAQ001', '2026-08-10 10:30:00', 'simulado', 1.65, FALSE, 39.8),
('MAQ002', '2026-08-09 08:00:00', 'simulado', 1.5, FALSE, 245.0),
('MAQ002', '2026-08-09 16:00:00', 'simulado', 1.65, FALSE, 245.6),
('MAQ002', '2026-08-10 08:00:00', 'simulado', 1.8, FALSE, 246.2),
('MAQ002', '2026-08-10 10:30:00', 'simulado', 1.95, FALSE, 246.8),
('MAQ003', '2026-08-09 08:00:00', 'simulado', 1.1, FALSE, 32.0),
('MAQ003', '2026-08-09 16:00:00', 'simulado', 1.25, FALSE, 32.6),
('MAQ003', '2026-08-10 08:00:00', 'simulado', 1.4, FALSE, 33.2),
('MAQ003', '2026-08-10 10:30:00', 'simulado', 1.55, FALSE, 33.8),
('MAQ004', '2026-08-09 08:00:00', 'simulado', 1.3, FALSE, 29.0),
('MAQ004', '2026-08-09 16:00:00', 'simulado', 1.45, FALSE, 29.6),
('MAQ004', '2026-08-10 08:00:00', 'simulado', 1.6, FALSE, 30.2),
('MAQ004', '2026-08-10 10:30:00', 'simulado', 1.75, FALSE, 30.8),
('MAQ005', '2026-08-09 08:00:00', 'simulado', 1.8, FALSE, 35.0),
('MAQ005', '2026-08-09 16:00:00', 'simulado', 1.95, FALSE, 35.6),
('MAQ005', '2026-08-10 08:00:00', 'simulado', 2.1, FALSE, 36.2),
('MAQ005', '2026-08-10 10:30:00', 'simulado', 2.25, FALSE, 36.8),
('MAQ006', '2026-08-09 08:00:00', 'simulado', 1.4, FALSE, 31.0),
('MAQ006', '2026-08-09 16:00:00', 'simulado', 1.55, FALSE, 31.6),
('MAQ006', '2026-08-10 08:00:00', 'simulado', 1.7, FALSE, 32.2),
('MAQ006', '2026-08-10 10:30:00', 'simulado', 1.85, FALSE, 32.8),
('MAQ007', '2026-08-09 08:00:00', 'simulado', 1.3, FALSE, 37.0),
('MAQ007', '2026-08-09 16:00:00', 'simulado', 1.45, FALSE, 37.6),
('MAQ007', '2026-08-10 08:00:00', 'simulado', 1.6, FALSE, 38.2),
('MAQ007', '2026-08-10 10:30:00', 'simulado', 1.75, FALSE, 38.8),
('MAQ008', '2026-08-09 08:00:00', 'simulado', 4.8, FALSE, 268.0),
('MAQ008', '2026-08-09 16:00:00', 'simulado', 4.95, FALSE, 268.6),
('MAQ008', '2026-08-10 08:00:00', 'simulado', 5.5, FALSE, 269.2),
('MAQ008', '2026-08-10 10:30:00', 'simulado', 5.65, TRUE, 269.8),
('MAQ009', '2026-08-09 08:00:00', 'simulado', 4.3, FALSE, 33.0),
('MAQ009', '2026-08-09 16:00:00', 'simulado', 4.45, FALSE, 33.6),
('MAQ009', '2026-08-10 08:00:00', 'simulado', 5.0, FALSE, 34.2),
('MAQ009', '2026-08-10 10:30:00', 'simulado', 5.15, FALSE, 34.8);

-- =====================================================================
-- 7. HISTORIAL_ESTADO_MAQUINA -- traza de como llegaron a su estado
--    actual las maquinas que NO estan en 'OPERA'.
-- =====================================================================
INSERT INTO HISTORIAL_ESTADO_MAQUINA (maquina, estado_anterior, estado_nuevo, fecha, referencia_tipo, referencia_id) VALUES
('MAQ003', 'OPERA', 'MANTE', '2026-08-04 09:00:00', 'orden_mantenimiento', 'OM-2026-003'),
('MAQ006', 'OPERA', 'FALLO', '2026-07-10 14:20:00', 'reporte_falla', '5'),
('MAQ008', 'OPERA', 'FALLO', '2026-08-09 15:40:00', 'reporte_falla', '33'),
('MAQ009', 'OPERA', 'MANTE', '2026-08-06 11:00:00', 'manual', NULL),
('MAQ001', NULL, 'OPERA', '2026-08-01 00:00:00', 'manual', NULL),
('MAQ002', NULL, 'OPERA', '2026-08-01 00:00:00', 'manual', NULL),
('MAQ004', NULL, 'OPERA', '2026-08-01 00:00:00', 'manual', NULL),
('MAQ005', NULL, 'OPERA', '2026-08-01 00:00:00', 'manual', NULL),
('MAQ007', NULL, 'OPERA', '2026-08-01 00:00:00', 'manual', NULL);

-- =====================================================================
-- 9. HISTORIAL PROPIO PARA PERFILES "VACIOS" (NUEVO)
--    -----------------------------------------------------------------
--    NOM-002  (María López, ENCLN -- encargada de línea)
--    NOM-004  (Ana García, ADMIN, especialidad AOI)
--    NOM001   (Zacarías, ADMIN)
--    NOM-LDGR (Luis Gallardo, ADMIN)
--    NOM-SAU1 (Saul, ADMIN)
--    NOM-ALEX (Alex Zuñiga, ADMIN)
--
--    En la version anterior del script estas 6 personas SOLO aparecian
--    en TRABA_ORDE_PERSONAL (cuadrilla/supervision de los preventivos
--    de la seccion 4), pero TrabajadorDetalleView (client/apps/
--    mantenimiento/views.py) arma la ficha de /mantenimiento/
--    trabajadores/<numeroNomina>/ consultando SOLO:
--      ordenes  = GET /mantenimiento/v1/ordenes/list/?trabajador=...
--      reportes = GET /fallas/v1/reportes/list/?trabajador=...
--    es decir, filtra por el campo ORDEN_MANTENIMIENTO.trabajador y
--    REPORTE_FALLA.trabajador (el responsable/reportante principal),
--    NUNCA por la cuadrilla de TRABA_ORDE_PERSONAL. Por eso sus fichas
--    seguian en 0/0/0 aunque ya estuvieran "en el reparto".
--
--    Para cada una de las 6 personas se agrega:
--      a) 1 reporte de falla  (REPORTE_FALLA.trabajador = ella)
--      b) 1 orden correctiva YA CERRADA ligada a ese reporte (mismo
--         patron INSERT abierta + UPDATE de cierre, para disparar
--         tg_actualizar_mttr_orden)
--      c) 1 orden PREVENTIVA pendiente (para que la ficha tambien
--         muestre "Ordenes pendientes" ademas de cerradas)
--    Con eso cada ficha queda con: 1 falla reportada, 2 ordenes
--    asignadas (1 cerrada + 1 pendiente) y 2 maquinas atendidas.
--
--    Folios/IDs nuevos, sin chocar con nada de arriba:
--      REPORTE_FALLA.numeroRegistro : 34-39
--      ORDEN_MANTENIMIENTO.folio    : OM-2026-043 a OM-2026-054
--    Ambos rangos ya quedan cubiertos por los DELETE genericos de la
--    seccion 0 (">= 6" y ">= 'OM-2026-006'"), asi que el script sigue
--    siendo re-ejecutable sin tocar la limpieza.
--
--    NOTA sobre EMP0001 (daniel perez gomez): ese usuario NO viene en
--    beta4.sql -- se dio de alta despues, directo desde el formulario
--    de registro de la app. Este script no le mete historial porque no
--    hay forma de saber sus datos reales (correo/telefono/usuario) sin
--    pisar la cuenta real. Si quieres que tambien tenga actividad de
--    demo, dime y agrego un bloque igual a este apuntando a 'EMP0001'
--    (la fila ya existe en tu BD, asi que solo harian falta el REPORTE_
--    FALLA/ORDEN_MANTENIMIENTO, no un INSERT en TRABAJADOR).
-- =====================================================================

INSERT INTO REPORTE_FALLA (numeroRegistro, asunto, fechaResolucion, fechaCreacion, horaCreacion, tiempoParo, causaRaiz, descripcion, imagen, maquina, trabajador, tipo_severidad, estado_reporte) VALUES
(34, 'Vibración fuera de rango detectada en recorrido de piso', DATE_ADD('2026-02-09', INTERVAL 2 DAY), '2026-02-09', '08:45:00', 3, 'Rodillo de transportador con desalineación leve, detectado en recorrido de supervisión - causa raiz confirmada en diagnostico', 'Durante recorrido de piso se detectó vibración anormal en el transportador principal, se levantó reporte para atención preventiva', NULL, 'MAQ005', 'NOM-002', 'MEDIA', 'CERRA'),
(35, 'Rechazo elevado detectado en revisión de calidad AOI', DATE_ADD('2026-02-16', INTERVAL 3 DAY), '2026-02-16', '09:15:00', 4, 'Patrón de referencia desactualizado tras cambio de producto, confirmado en diagnostico de especialidad - causa raiz confirmada en diagnostico', 'Como especialista en AOI se detectó un incremento en el porcentaje de rechazo durante auditoría de calidad, se generó orden correctiva', NULL, 'MAQ003', 'NOM-004', 'ALTA', 'CERRA'),
(36, 'Alarma de comunicación intermitente con el módulo de monitoreo', DATE_ADD('2026-02-23', INTERVAL 2 DAY), '2026-02-23', '10:05:00', 2, 'Cable de red del sensor con falso contacto, identificado al revisar logs del modulo - causa raiz confirmada en diagnostico', 'Se detectó pérdida intermitente de lecturas del sensor de vibración al revisar el panel de monitoreo, se generó reporte para revisión', NULL, 'MAQ001', 'NOM001', 'BAJA', 'CERRA'),
(37, 'Ruido anormal reportado por operador en estación de prueba', DATE_ADD('2026-03-02', INTERVAL 3 DAY), '2026-03-02', '11:20:00', 5, 'Ventilador interno de la estación con desgaste en balero, confirmado en diagnostico - causa raiz confirmada en diagnostico', 'Operador reportó ruido inusual en la estación de prueba durante turno matutino, se validó y escaló a orden correctiva', NULL, 'MAQ006', 'NOM-LDGR', 'MEDIA', 'CERRA'),
(38, 'Fuga menor de aire detectada en inspección de rutina', DATE_ADD('2026-03-09', INTERVAL 2 DAY), '2026-03-09', '07:50:00', 3, 'Conexión neumática de la boquilla con o-ring deteriorado, confirmado en diagnostico - causa raiz confirmada en diagnostico', 'Durante inspección de rutina de línea se detectó una fuga de aire menor en el dispensador de pasta, se generó reporte', NULL, 'MAQ004', 'NOM-SAU1', 'BAJA', 'CERRA'),
(39, 'Retraso en ciclo detectado durante revisión de rendimiento', DATE_ADD('2026-03-16', INTERVAL 4 DAY), '2026-03-16', '12:35:00', 6, 'Driver del eje X con firmware desactualizado, confirmado en diagnostico - causa raiz confirmada en diagnostico', 'Al revisar los tiempos de ciclo de la línea 1 se detectó un retraso sostenido en el Pick & Place, se generó reporte correctivo', NULL, 'MAQ001', 'NOM-ALEX', 'MEDIA', 'CERRA');

INSERT INTO TIPO_REPORTE (tipo_falla, reporte_falla) VALUES
(1, 34),
(5, 35),
(2, 36),
(1, 37),
(3, 38),
(4, 39);

-- Igual que en la seccion 2: se insertan ABIERTAS y se cierran con
-- UPDATE aparte para disparar tg_actualizar_mttr_orden.
INSERT INTO ORDEN_MANTENIMIENTO (folio, descripcion, diagnostico, notas, fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre, horasIntervenidas, porcentaje, imagen, maquina, trabajador, reporte_falla, tipo_mantenimiento, estado_orden) VALUES
('OM-2026-043', 'Atención correctiva: vibración fuera de rango en recorrido de piso', 'Rodillo de transportador con desalineación leve, detectado en recorrido de supervisión', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-02-09', '2026-02-09', '08:45:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ005', 'NOM-002', 34, 'CORRE', 'ENPRO'),
('OM-2026-044', 'Atención correctiva: rechazo elevado detectado en revisión de calidad AOI', 'Patrón de referencia desactualizado tras cambio de producto', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-02-16', '2026-02-16', '09:15:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ003', 'NOM-004', 35, 'CORRE', 'ENPRO'),
('OM-2026-045', 'Atención correctiva: alarma de comunicación intermitente con monitoreo', 'Cable de red del sensor con falso contacto', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-02-23', '2026-02-23', '10:05:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ001', 'NOM001', 36, 'CORRE', 'ENPRO'),
('OM-2026-046', 'Atención correctiva: ruido anormal en estación de prueba', 'Ventilador interno de la estación con desgaste en balero', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-02', '2026-03-02', '11:20:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ006', 'NOM-LDGR', 37, 'CORRE', 'ENPRO'),
('OM-2026-047', 'Atención correctiva: fuga menor de aire en dispensador de pasta', 'Conexión neumática de la boquilla con o-ring deteriorado', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-09', '2026-03-09', '07:50:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ004', 'NOM-SAU1', 38, 'CORRE', 'ENPRO'),
('OM-2026-048', 'Atención correctiva: retraso en ciclo del Pick & Place', 'Driver del eje X con firmware desactualizado', 'Repuesto/ajuste realizado, se valida funcionamiento antes de reincorporar la máquina a producción.', '2026-03-16', '2026-03-16', '12:35:00', NULL, NULL, NULL, 100.00, NULL, 'MAQ001', 'NOM-ALEX', 39, 'CORRE', 'ENPRO');

UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-02-09', INTERVAL 2 DAY), horaCierre = '10:30:00', horasIntervenidas = 2.0, estado_orden = 'CERRA' WHERE folio = 'OM-2026-043';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-02-16', INTERVAL 3 DAY), horaCierre = '11:45:00', horasIntervenidas = 2.75, estado_orden = 'CERRA' WHERE folio = 'OM-2026-044';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-02-23', INTERVAL 2 DAY), horaCierre = '12:00:00', horasIntervenidas = 1.25, estado_orden = 'CERRA' WHERE folio = 'OM-2026-045';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-02', INTERVAL 3 DAY), horaCierre = '13:15:00', horasIntervenidas = 3.0, estado_orden = 'CERRA' WHERE folio = 'OM-2026-046';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-09', INTERVAL 2 DAY), horaCierre = '09:40:00', horasIntervenidas = 1.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-047';
UPDATE ORDEN_MANTENIMIENTO SET fechaCierre = DATE_ADD('2026-03-16', INTERVAL 4 DAY), horaCierre = '14:20:00', horasIntervenidas = 3.5, estado_orden = 'CERRA' WHERE folio = 'OM-2026-048';

INSERT INTO TAREA_ORDEN (tarea, orden_mantenimiento, fechaInicio, fechaCierre, horaInicio, horafin, verificacion, observaciones) VALUES
(1, 'OM-2026-043', '2026-02-09', DATE_ADD('2026-02-09', INTERVAL 2 DAY), '08:45:00', '10:30:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(3, 'OM-2026-044', '2026-02-16', DATE_ADD('2026-02-16', INTERVAL 3 DAY), '09:15:00', '11:45:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(2, 'OM-2026-045', '2026-02-23', DATE_ADD('2026-02-23', INTERVAL 2 DAY), '10:05:00', '12:00:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(5, 'OM-2026-046', '2026-03-02', DATE_ADD('2026-03-02', INTERVAL 3 DAY), '11:20:00', '13:15:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(4, 'OM-2026-047', '2026-03-09', DATE_ADD('2026-03-09', INTERVAL 2 DAY), '07:50:00', '09:40:00', TRUE, 'Verificado y documentado, sin observaciones pendientes'),
(1, 'OM-2026-048', '2026-03-16', DATE_ADD('2026-03-16', INTERVAL 4 DAY), '12:35:00', '14:20:00', TRUE, 'Verificado y documentado, sin observaciones pendientes');

INSERT INTO HERRA_ORDEN (herramienta, orden_mantenimiento) VALUES
(2, 'OM-2026-043'),
(1, 'OM-2026-044'),
(2, 'OM-2026-045'),
(3, 'OM-2026-046'),
(1, 'OM-2026-047'),
(3, 'OM-2026-048');

-- Cuadrilla: cada quien "propio" con un tecnico de apoyo, para que se
-- vea realista (un admin/encargado no repara solo en la mayoria de
-- los casos, pero SI queda como responsable/trabajador principal).
INSERT INTO TRABA_ORDE_PERSONAL (trabajador, orden_mantenimiento) VALUES
('NOM-002', 'OM-2026-043'), ('NOM-XD1', 'OM-2026-043'),
('NOM-004', 'OM-2026-044'), ('NOM-003', 'OM-2026-044'),
('NOM001', 'OM-2026-045'), ('NOM-GALL', 'OM-2026-045'),
('NOM-LDGR', 'OM-2026-046'), ('NOM-SAU2', 'OM-2026-046'),
('NOM-SAU1', 'OM-2026-047'), ('NOM-001', 'OM-2026-047'),
('NOM-ALEX', 'OM-2026-048'), ('NOM-ZUNI', 'OM-2026-048');

-- Preventivo pendiente adicional para cada uno (asi la ficha tambien
-- muestra "Ordenes pendientes" y no solo cerradas). Fechas despues del
-- 26-ago para no encimarse con los 9 de la seccion 4.
INSERT INTO ORDEN_MANTENIMIENTO (folio, descripcion, diagnostico, notas, fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre, horasIntervenidas, porcentaje, imagen, maquina, trabajador, reporte_falla, tipo_mantenimiento, estado_orden) VALUES
('OM-2026-049', 'Mantenimiento preventivo: inspección de banda y sensores tras hallazgo de recorrido de piso', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-27', '2026-08-05', '09:30:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ002', 'NOM-002', NULL, 'PREVE', 'SOLIC'),
('OM-2026-050', 'Mantenimiento preventivo: recalibración de patrón AOI de referencia', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-28', '2026-08-05', '10:30:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ009', 'NOM-004', NULL, 'PREVE', 'APROB'),
('OM-2026-051', 'Mantenimiento preventivo: revisión de cableado de sensores de monitoreo', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-08-31', '2026-08-05', '11:30:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ007', 'NOM001', NULL, 'PREVE', 'PROGR'),
('OM-2026-052', 'Mantenimiento preventivo: lubricación y verificación de balero de ventilador', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-09-01', '2026-08-05', '12:30:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ008', 'NOM-LDGR', NULL, 'PREVE', 'SOLIC'),
('OM-2026-053', 'Mantenimiento preventivo: reemplazo preventivo de o-rings neumáticos', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-09-02', '2026-08-05', '13:30:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ005', 'NOM-SAU1', NULL, 'PREVE', 'APROB'),
('OM-2026-054', 'Mantenimiento preventivo: actualización de firmware de drivers de eje', NULL, 'Orden generada por plan de mantenimiento preventivo, pendiente de ejecución', '2026-09-03', '2026-08-05', '14:30:00', NULL, NULL, NULL, 0.00, NULL, 'MAQ003', 'NOM-ALEX', NULL, 'PREVE', 'PROGR');

INSERT INTO TAREA_ORDEN (tarea, orden_mantenimiento, fechaInicio, fechaCierre, horaInicio, horafin, verificacion, observaciones) VALUES
(2, 'OM-2026-049', '2026-08-27', NULL, '09:30:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-27'),
(3, 'OM-2026-050', '2026-08-28', NULL, '09:30:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-28'),
(4, 'OM-2026-051', '2026-08-31', NULL, '09:30:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-08-31'),
(5, 'OM-2026-052', '2026-09-01', NULL, '09:30:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-09-01'),
(1, 'OM-2026-053', '2026-09-02', NULL, '09:30:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-09-02'),
(2, 'OM-2026-054', '2026-09-03', NULL, '09:30:00', NULL, NULL, 'Pendiente de ejecución, programado para el 2026-09-03');

INSERT INTO HERRA_ORDEN (herramienta, orden_mantenimiento) VALUES
(1, 'OM-2026-049'),
(2, 'OM-2026-050'),
(3, 'OM-2026-051'),
(1, 'OM-2026-052'),
(2, 'OM-2026-053'),
(3, 'OM-2026-054');

INSERT INTO TRABA_ORDE_PERSONAL (trabajador, orden_mantenimiento) VALUES
('NOM-002', 'OM-2026-049'), ('NOM-XD1', 'OM-2026-049'),
('NOM-004', 'OM-2026-050'), ('NOM-ZUNI', 'OM-2026-050'),
('NOM001', 'OM-2026-051'), ('NOM-GALL', 'OM-2026-051'),
('NOM-LDGR', 'OM-2026-052'), ('NOM-SAU2', 'OM-2026-052'),
('NOM-SAU1', 'OM-2026-053'), ('NOM-003', 'OM-2026-053'),
('NOM-ALEX', 'OM-2026-054'), ('NOM-001', 'OM-2026-054');

-- =====================================================================
-- 9. STOCK DE REFACCIONES EN ALERTA (DATOS PARA DEMO)
-- =====================================================================
-- La vista v_kpi_stock muestra únicamente refacciones cuyo stock sea
-- menor o igual a stockMinimo. Los datos originales de beta4.sql tenían
-- todas las refacciones por encima de su mínimo, por lo que el dashboard
-- mostraba "Sin datos por ahora".
--
-- Estos valores son intencionales para la demostración:
--   Rodamiento 6205  -> 2 / mínimo 3 -> faltan 1
--   Nozzle 0402      -> 5 / mínimo 8 -> faltan 3
--   Sensor óptico    -> 1 / mínimo 2 -> faltan 1
--
-- Se usan UPDATE para que el script siga siendo re-ejecutable.

UPDATE REFACCION
SET stock = 2
WHERE codigoSku = 'SKU-6205-001';

UPDATE REFACCION
SET stock = 5
WHERE codigoSku = 'SKU-NZ0402';

UPDATE REFACCION
SET stock = 1
WHERE codigoSku = 'SKU-SPR10';

-- Mantener sincronizado el estado de inventario del seed original.
UPDATE ESTADO_REFACCION
SET cantidad = 2
WHERE refaccion = 1
  AND estado_refaccion = 'DISPO';

UPDATE ESTADO_REFACCION
SET cantidad = 5
WHERE refaccion = 2
  AND estado_refaccion = 'DISPO';

UPDATE ESTADO_REFACCION
SET cantidad = 1
WHERE refaccion = 3
  AND estado_refaccion = 'ENREP';

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
-- LLAMADAS DE EJEMPLO PARA DEMOSTRAR LOS SP EN VIVO DURANTE LA
-- PRESENTACION (no se ejecutan automaticamente, son solo referencia)
-- =====================================================================
-- call sp_resumen_maquina_maquinaria('MAQ008', @n, @e, @tf, @to, @h, @m1, @m2, @d);
-- select @n, @e, @tf, @to, @h, @m1, @m2, @d;
--
-- call sp_resumen_maquina('MAQ001', @n, @e, @mtbf, @mttr, @dispo, @h, @f, @i, @r);
-- select @n, @e, @mtbf, @mttr, @dispo, @h, @f, @i, @r;
--
-- call sp_historial_maquina('MAQ001');
--
-- call sp_rendimiento_trabajador('NOM-ALEX', @nombre, @asignadas, @cerradas);
-- select @nombre, @asignadas, @cerradas;
--
-- set @factor = 0.08;
-- call sp_calcular_depreciacion_pieza('PS-YPK2-002', @factor);
-- select @factor;
--
-- call sp_registrar_salida_refaccion(2, 'OM-2026-034', 'Boquilla usada en preventivo', '2026-08-12', '10:00:00', 'PS-YPK2-002');
-- select * from REFACCION where numeroRegistro = 2;
--
-- call sp_reporte_disponibilidad_planta('2026-01-01', '2026-08-10');
--
-- call sp_cerrar_periodo_indicador('MAQ001', '2026-08-10');
-- select * from INDICADOR where maquina = 'MAQ001' order by numeroRegistro desc;

-- =====================================================================
-- FIN DEL SCRIPT DE CARGA DE DATOS PARA DEMO
-- =====================================================================

SELECT 'seed_demo.sql OK -- datos cargados/reemplazados correctamente' AS status,
       (SELECT COUNT(*) FROM MAQUINA) AS maquinas,
       (SELECT COUNT(*) FROM LINEA) AS lineas,
       (SELECT COUNT(*) FROM REPORTE_FALLA) AS reportes_falla,
       (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO) AS ordenes,
       (SELECT COUNT(*) FROM ORDEN_MANTENIMIENTO WHERE fechaProgramada >= '2026-08-11') AS mantenimientos_programados,
       (SELECT COUNT(*) FROM TRABAJADOR) AS usuarios,
       (SELECT COUNT(DISTINCT trabajador) FROM ORDEN_MANTENIMIENTO WHERE trabajador IS NOT NULL) AS trabajadores_con_orden_propia,
       (SELECT COUNT(DISTINCT trabajador) FROM REPORTE_FALLA) AS trabajadores_con_falla_reportada;