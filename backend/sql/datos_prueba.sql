
INSERT INTO TIPO_PIEZA (nombre, descripcion) VALUES
('Cabezal', 'Cabezal de pickup para colocar componentes en PCB');

INSERT INTO EDO_PIEZA (codigo, nombre, descripcion) VALUES
('OPERA', 'Operativa', 'Pieza en condiciones normales de funcionamiento');

INSERT INTO EDO_REFACCION (codigo, nombre, descripcion) VALUES
('DISPO', 'Disponible', 'Refacción disponible en almacén'); 

INSERT INTO TIPO_REFACCION (nombre, descripcion) VALUES
('Rodamiento', 'Rodamiento para ejes y motores');

INSERT INTO CLASIFICACION (codigo, nombre, descripcion) VALUES
('ALTA', 'Alta', 'Su falta afecta el rendimiento de la máquina pero no la detiene completamente');

INSERT INTO PROVEEDOR (codigo, rfc, razonSocial, nombreComercial, telefono, email, dirCalle, dirCodigoPostal, dirNumero, contNombre, contApellPat, contApellMat) VALUES
('PROV001', 'YAM850101ABC', 'Yamaha Motor de México S.A. de C.V.', 'Yamaha SMT', '5551234567', 'ventas@yamaha-smt.mx', 'Av. Industrial', '02870', '1500', 'Roberto', 'García', 'López');

INSERT INTO PLANTA (codigo, nombre, descripcion, ubicacion) VALUES
('PLT001', 'Planta EMS Central', 'Planta de ensamble de componentes de cómputo', 'Ciudad de México, México'); --

INSERT INTO MARCA (clave, nombre, descripcion) VALUES
('YAMHA', 'Yamaha', 'Fabricante japonés de máquinas SMT'); 

INSERT INTO TIPO_MAQUINA (nombre, descripcion) VALUES
('Pick & Place', 'Máquina para colocar componentes electrónicos en PCB');

INSERT INTO EDO_MAQUINA (codigo, nombre, descripcion) VALUES
('OPERA', 'Operativa', 'Máquina en condiciones normales de funcionamiento');

INSERT INTO ROL (codigo, nombre, descripcion) VALUES
('TECNI', 'Técnico', 'Técnico de mantenimiento');

INSERT INTO ESPECIALIDAD (codigo, nombre, descripcion) VALUES
('SMT', 'Surface Mount Technology', 'Especialidad en tecnología de montaje superficial');

INSERT INTO TIPO_FALLA (nombre, descripcion) VALUES
('Mecánica', 'Fallo en componentes mecánicos');

INSERT INTO TIPO_SEVERIDAD (codigo, nombre, descripcion) VALUES
('MEDIA', 'Media', 'Fallo que afecta parcialmente la operación');

INSERT INTO EDO_REPORTE (codigo, nombre, descripcion) VALUES
('ABIER', 'Abierto', 'Reporte recién o parcialmente creado, sin atención');

INSERT INTO TIPO_MANTENIMIENTO (codigo, nombre, descripcion) VALUES
('CORRE', 'Correctivo', 'Mantenimiento para corregir una falla existente');

INSERT INTO ESTADO_ORDEN (codigo, nombre, descripcion) VALUES
('PENDI', 'Pendiente', 'Orden creada, pendiente de ejecución');

INSERT INTO TIPO_MOVIMIENTO (codigo, descripcion) VALUES
('INSTA', 'Instalación de refacción como pieza en máquina');

INSERT INTO EDO_HERRAMIENTA (codigo, nombre, descripcion) VALUES
('DISPO', 'Disponible', 'Herramienta lista para uso');

INSERT INTO TIPO_HERRAMIENTA (nombre, descripcion) VALUES
('Herramienta manual', 'Herramientas de uso manual como llaves y destornilladores');

INSERT INTO TAREAS (instruccion, actividad) VALUES
('Verificar alineación del cabezal', TRUE);

INSERT INTO AREA (codigo, nombre, descripcion, telefono, planta) VALUES
('ARR001', 'Área de Montaje SMT', 'Zona de ensamble superficial de componentes', '5551234568', 'PLT001');

INSERT INTO MODELO (codigo, nombre, descripcion, marca) VALUES
('YPK2', 'YPK Pick & Place', 'Modelo de alta velocidad para componentes 0201', 'YAMHA');

INSERT INTO REFACCION (nombre, codigoSku, puntoReorden, codigoInventario, numeroOrden, costo, tiempoEntregaApr, stock, stockMinimo, proveedor, tipo_refaccion, clasificacion) VALUES
('Rodamiento 6205', 'SKU-6205-001', 5, 'INV-6205', 'ORD-2026-001', 125.50, 7, 15, 3, 'PROV001', 1, 'ALTA');

INSERT INTO TRABAJADOR (numeroNomina, nombre, apellidoPat, apellidoMat, telefono, correo, usuario, `contraseña`, actividad, rol, especialidad) VALUES
('NOM-001', 'Juan', 'Pérez', 'García', '5559876543', 'juan.perez@ems.mx', 'jperez', 'password123', TRUE, 'TECNI', 'SMT');

INSERT INTO HERRAMIENTA (nombre, descripcion, imagen, tipo_herramienta) VALUES
('Juego de llaves Allen', 'Juego de llaves Allen del #1 al #10', '/img/herramientas/llaves_allen.jpg', 1);


INSERT INTO LINEA (codigo, nombre, descripcion, area) VALUES
('LI001', 'Línea de Producción 1', 'Primera línea de ensamble SMT', 'ARR001');

INSERT INTO ESTADO_REFACCION (estado_refaccion, refaccion, cantidad) VALUES
('DISPO', 1, 15);

INSERT INTO ESTADO_HERRAMIENTA (herramienta, edo_herramienta, cantidad) VALUES
(1, 'DISPO', 5);


INSERT INTO MAQUINA (codigo, numeroSerie, nombre, descripcion, imagen_url, fechaInstalacion, linea, marca, modelo, estado_maquina, tipo_maquina) VALUES
('MAQ001', 'SN-YAM-YPK2-001', 'Pick & Place Principal', 'Máquina de alta velocidad para colocación de componentes SMT', '/img/maquinas/pick_place_01.jpg', '2020-01-15', 'LI001', 'YAMHA', 'YPK2', 'OPERA', 1);

INSERT INTO INDICADOR (fechaInicio, fechaFin, mttr, mtbf, porcentajeDispo, maquina) VALUES
('2026-01-01', '2026-01-31', 2.5, 104.0, 98, 'MAQ001');

--Eliminar refaccion
INSERT INTO PIEZA (numeroSerie, codigoEtiqueta, nombre, costoInicial, horasOperacion, tiempoVidaUtil, depresacionAnual, valorResidual, fechaInstalacion, fechaGarantia, edo_pieza, maquina, tipo_pieza) VALUES
('PS-6205-001', 'ETQ-6205-001', 'Rodamiento Cabezal Principal', 125.50, 2500, 10000, 10.05, 25.00, '2026-06-01', '2028-06-01', 'OPERA', 'MAQ001', 1);

INSERT INTO REGISTRO_OPS (fechaInicio, fechaFin, horasOperacion, maquina) VALUES
('2026-01-01', '2026-01-31', 208, 'MAQ001');

INSERT INTO REFACC_MAQUI (maquina, refaccion) VALUES
('MAQ001', 1);

INSERT INTO REPORTE_FALLA (numeroRegistro, asunto, fechaResolucion, fechaCreacion, horaCreacion, tiempoParo, causaRaiz, descripcion, imagen, maquina, trabajador, tipo_falla, tipo_severidad) VALUES
(1, 'Ruido anormal en cabezal de pickup', '2026-01-20', '2026-01-20', '08:30:00', 2, 'Desgaste de rodamiento del eje principal', 'Se detectó ruido metálico al operar el cabezal a alta velocidad', '/img/reportes/ruido_cabezal.jpg', 'MAQ001', 'NOM-001', 1, 'MEDIA'); -- fecha cierre


INSERT INTO ORDEN_MANTENIMIENTO (folio, descripcion, diagnostico, notas, fechaProgramada, fechaCreacion, horaCreacion, fechaCierre, horaCierre, horasIntervenidas, imagen, maquina, trabajador, reporte_falla, tipo_mantenimiento, estado_orden) VALUES
('OM-2026-001', 'Reemplazo de rodamiento en cabezal', 'Rodamiento 6205 con desgaste avanzado', 'Se reemplazó con refacción del almacén', '2026-01-22', '2026-01-20', '09:00:00', '2026-01-22', '11:30:00', 2.5, '/img/ordenes/om_2026_001.jpg', 'MAQ001', 'NOM-001', 1, 'COR', 'PEN'); -- Null en fecha programada

INSERT INTO MOVIMIENTO (numeroRegistro, descripcion, fecha, hora, tipoMovimiento, orden_mantenimiento, refaccion, PIEZA) VALUES
(1, 'Instalación de rodamiento 6205 en cabezal', '2026-01-22', '10:15:00', 'INSTA', 'OM-2026-001', 1, 1); -- Pueden ser nulleables

INSERT INTO TRABA_ORDE_PERSONAL (trabajador, orden_mantenimiento) VALUES
('NOM-001', 'OM-2026-001');

INSERT INTO TAREA_ORDEN (tarea, orden_mantenimiento, porcentaje, fechaInicio, fechaCierre, horaInicio, horafin, verificacion, observaciones) VALUES
(1, 'OM-2026-001', 100.00, '2026-01-22', '2026-01-22', '09:30:00', '11:00:00', TRUE, 'Verificación exitosa, alineación correcta'); 

INSERT INTO HERRA_ORDEN (herramienta, orden_mantenimiento) VALUES
(1, 'OM-2026-001');

