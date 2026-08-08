-- =============================================================================
-- CONSULTAS AVANZADAS DEL ASISTENTE ELIPSE (OperaCore CMMS)
-- Archivo de origen: cmms/api/apps/elipse/views.py
-- Función principal: _resolve() [Líneas 811 - 1160] y funciones auxiliares
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. TOP N MÁQUINAS CON MÁS FALLAS
-- Ubicación: Líneas 1005 - 1008 (dentro de _resolve(), intent 'top_maquinas_fallas')
-- Qué resuelve: Identifica las máquinas con mayor número de reportes de falla.
-- JOINs / Agregación: MAQUINA JOIN REPORTE_FALLA + GROUP BY + ORDER BY
-- -----------------------------------------------------------------------------
SELECT 
    m.codigo, 
    m.nombre, 
    COUNT(r.numeroRegistro) AS TotalFallas
FROM MAQUINA m
JOIN REPORTE_FALLA r ON r.maquina = m.codigo
GROUP BY m.codigo, m.nombre
ORDER BY TotalFallas DESC
LIMIT 5; -- Nota: El límite es dinámico en código (default 5, configurable por variable top_n)


-- -----------------------------------------------------------------------------
-- 2. RANKING DE TÉCNICOS POR ÓRDENES CERRADAS
-- Ubicación: Líneas 1061 - 1065 (dentro de _resolve(), intent 'top_tecnicos')
-- Qué resuelve: Evalúa el desempeño y carga de trabajo resuelta por cada técnico.
-- JOINs / Agregación: TRABAJADOR JOIN ORDEN_MANTENIMIENTO + GROUP BY + ORDER BY
-- -----------------------------------------------------------------------------
SELECT 
    t.numeroNomina,
    CONCAT(t.nombre, ' ', t.apellidoPat, ' ', COALESCE(t.apellidoMat, '')) AS Nombre,
    COUNT(o.folio) AS OrdenesCerradas
FROM TRABAJADOR t
JOIN ORDEN_MANTENIMIENTO o ON o.trabajador = t.numeroNomina
WHERE o.estado_orden = 'CERRA'
GROUP BY t.numeroNomina, t.nombre, t.apellidoPat, t.apellidoMat
ORDER BY OrdenesCerradas DESC
LIMIT 5; -- Límite dinámico configurable en el backend


-- -----------------------------------------------------------------------------
-- 3. DISTRIBUCIÓN DE TRABAJADORES POR ROL
-- Ubicación: Líneas 1127 - 1135 (dentro de _resolve(), intent 'trabajadores')
-- Qué resuelve: Resume la plantilla laboral agrupada por puesto/rol de trabajo.
-- JOINs / Agregación: TRABAJADOR LEFT JOIN ROL + GROUP BY + ORDER BY
-- -----------------------------------------------------------------------------
SELECT 
    COALESCE(r.nombre, 'Sin Rol') AS Rol,
    COUNT(t.numeroNomina) AS Total
FROM TRABAJADOR t
LEFT JOIN ROL r ON t.rol = r.codigo
GROUP BY r.nombre
ORDER BY Total DESC;


-- -----------------------------------------------------------------------------
-- 4. REFACCIONES USADAS EN UNA FALLA (VÍA ORDEN DE MANTENIMIENTO)
-- Ubicación: Líneas 1533 - 1536 (función auxiliar en views.py)
-- Qué resuelve: Muestra los repuestos/refacciones consumidos para atender una falla.
-- JOINs / Agregación: ORDEN_MANTENIMIENTO JOIN MOVIMIENTO JOIN REFACCION + GROUP BY
-- -----------------------------------------------------------------------------
SELECT 
    rf.codigoSku,
    rf.nombre AS Refaccion,
    COUNT(m.numeroRegistro) AS CantidadUsada
FROM ORDEN_MANTENIMIENTO o
JOIN MOVIMIENTO m ON m.orden_mantenimiento = o.folio
JOIN REFACCION rf ON m.refaccion = rf.numeroRegistro
WHERE o.reporte_falla = 1 -- Sustituir '1' por el ID/número de reporte de falla deseado
GROUP BY rf.codigoSku, rf.nombre;


-- -----------------------------------------------------------------------------
-- 5. ÚLTIMOS INDICADORES (MTBF / MTTR / DISPONIBILIDAD) DE UNA MÁQUINA
-- Ubicación: Líneas 941 - 943 (dentro de _resolve(), intent 'indicadores_maquina')
-- Qué resuelve: Muestra la métrica más reciente de rendimiento y confiabilidad de un equipo.
-- JOINs / Agregación: INDICADOR JOIN MAQUINA + ORDER BY fechaFin DESC LIMIT
-- -----------------------------------------------------------------------------
SELECT 
    i.mtbf AS MTBF_Horas,
    i.mttr AS MTTR_Horas,
    i.porcentajeDispo AS Disponibilidad_Pct,
    i.fechaInicio,
    i.fechaFin
FROM INDICADOR i
JOIN MAQUINA m ON i.maquina = m.codigo
WHERE m.codigo = 'MAQ001' -- Sustituir 'MAQ001' por el código de la máquina
ORDER BY i.fechaFin DESC
LIMIT 1;


-- -----------------------------------------------------------------------------
-- 6. LISTADO DE MÁQUINAS CON ESTADO, LÍNEA, MARCA Y MODELO
-- Ubicación: Líneas 889-893 y 921-923 (dentro de _resolve(), intents 'maquinas_falla' / 'maquinas_mantenimiento')
-- Qué resuelve: Muestra la información descriptiva y de ubicación de los equipos.
-- JOINs / Agregación: 4 LEFT JOIN encadenados (EDO_MAQUINA, LINEA, MARCA, MODELO)
-- -----------------------------------------------------------------------------
SELECT 
    m.codigo,
    m.nombre AS Maquina,
    e.nombre AS Estado,
    l.nombre AS Linea,
    mar.nombre AS Marca,
    mod.nombre AS Modelo
FROM MAQUINA m
LEFT JOIN EDO_MAQUINA e ON m.estado_maquina = e.codigo
LEFT JOIN LINEA l ON m.linea = l.codigo
LEFT JOIN MARCA mar ON m.marca = mar.clave
LEFT JOIN MODELO mod ON m.modelo = mod.codigo
WHERE m.estado_maquina = 'FALLO'; -- Filtrable por 'FALLO', 'MANTE', 'OPERA', etc.


-- -----------------------------------------------------------------------------
-- 7. ÓRDENES DE UNA MÁQUINA CON ESTADO, TIPO Y TÉCNICO ASIGNADO
-- Ubicación: Líneas 1019 - 1024 (dentro de _resolve(), intent 'ordenes_pendientes' / 'ordenes_maquina')
-- Qué resuelve: Rastrea la trazabilidad del mantenimiento preventivo/correctivo de una máquina.
-- JOINs / Agregación: ORDEN_MANTENIMIENTO + 4 LEFT JOIN
-- -----------------------------------------------------------------------------
SELECT 
    o.folio,
    o.descripcion,
    eo.nombre AS Estado,
    tm.nombre AS TipoMantenimiento,
    CONCAT(t.nombre, ' ', t.apellidoPat) AS Tecnico,
    o.fechaProgramada
FROM ORDEN_MANTENIMIENTO o
LEFT JOIN ESTADO_ORDEN eo ON o.estado_orden = eo.codigo
LEFT JOIN TIPO_MANTENIMIENTO tm ON o.tipo_mantenimiento = tm.codigo
LEFT JOIN TRABAJADOR t ON o.trabajador = t.numeroNomina
LEFT JOIN MAQUINA m ON o.maquina = m.codigo
WHERE o.maquina = 'MAQ001' -- Opcional: Filtrar por máquina o por estado 'PENDI'/'ENPRO'
ORDER BY o.fechaCreacion DESC;


-- -----------------------------------------------------------------------------
-- 8. REPORTES DE FALLA CON SEVERIDAD, ESTADO, MÁQUINA Y TRABAJADOR
-- Ubicación: Líneas 964 - 968 (dentro de _resolve(), intent 'fallas_abiertas' / 'fallas_criticas')
-- Qué resuelve: Consulta detallada de averías registradas en planta.
-- JOINs / Agregación: REPORTE_FALLA + 4 LEFT JOIN
-- -----------------------------------------------------------------------------
SELECT 
    rf.numeroRegistro AS Folio,
    rf.asunto,
    m.nombre AS Maquina,
    ts.nombre AS Severidad,
    er.nombre AS Estado,
    CONCAT(t.nombre, ' ', t.apellidoPat) AS ReportadoPor,
    rf.fechaCreacion
FROM REPORTE_FALLA rf
LEFT JOIN MAQUINA m ON rf.maquina = m.codigo
LEFT JOIN TIPO_SEVERIDAD ts ON rf.tipo_severidad = ts.codigo
LEFT JOIN EDO_REPORTE er ON rf.estado_reporte = er.codigo
LEFT JOIN TRABAJADOR t ON rf.trabajador = t.numeroNomina
WHERE rf.estado_reporte IN ('ABIER', 'ENATE') -- Filtrable según la intención (e.g. severidad 'CRITI')
ORDER BY rf.fechaCreacion DESC;


-- -----------------------------------------------------------------------------
-- 9. HISTORIAL DE FALLAS POR MÁQUINA (PARA EL ASISTENTE ELIPSE)
-- Ubicación: Líneas 1511 - 1521 (Función _historial_fallas_maquina)
-- Qué resuelve: Alimenta el contexto de la IA/asistente con el historial reciente de un equipo.
-- JOINs / Agregación: REPORTE_FALLA LEFT JOIN TIPO_SEVERIDAD + ORDER BY ... LIMIT
-- -----------------------------------------------------------------------------
SELECT 
    rf.numeroRegistro,
    rf.asunto,
    rf.fechaCreacion,
    ts.nombre AS Severidad,
    rf.causaRaiz
FROM REPORTE_FALLA rf
LEFT JOIN TIPO_SEVERIDAD ts ON rf.tipo_severidad = ts.codigo
WHERE rf.maquina = 'MAQ001' -- Código de la máquina consultada
ORDER BY rf.fechaCreacion DESC
LIMIT 10;


-- -----------------------------------------------------------------------------
-- 10. HERRAMIENTAS CON SU TIPO Y ESTADO
-- Ubicación: Líneas 1113 - 1115 (dentro de _resolve(), intent 'herramientas')
-- Qué resuelve: Consulta el catálogo de herramientas y su categorización técnica.
-- JOINs / Agregación: HERRAMIENTA JOIN TIPO_HERRAMIENTA
-- -----------------------------------------------------------------------------
SELECT 
    h.numeroRegistro,
    h.nombre AS Herramienta,
    th.nombre AS TipoHerramienta
FROM HERRAMIENTA h
JOIN TIPO_HERRAMIENTA th ON h.tipo_herramienta = th.numeroRegistro;