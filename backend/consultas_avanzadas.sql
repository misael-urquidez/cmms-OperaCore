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

-- =============================================================================
-- SUBCONSULTAS ADICIONALES (CA-14 A CA-20)
-- -----------------------------------------------------------------------------
-- Las consultas CA-11 y CA-12 (subconsultas escalares en SELECT) viven dentro
-- de sp_reporte_disponibilidad_planta (sp.sql), y la CA-13 (subconsulta
-- correlacionada con MAX) dentro de v_kpi_indicadores_actuales y
-- v_kpi_monitoreo_predictivo (vistas_kpi.sql). Aquí se anexan las variantes
-- que completan los tipos de subconsulta requeridos para la evidencia.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 14. MÁQUINAS CON AL MENOS UNA ORDEN DE MANTENIMIENTO (SUBCONSULTA CON IN)
-- Ubicación: documentacion-consultas-vistas.md, consulta avanzada CA-14
-- Qué resuelve: Identifica qué equipos tienen historial de mantenimiento.
-- Apoya a: sp_resumen_maquina (sp.sql)
-- JOINs / Agregación: MAQUINA + subconsulta IN (SELECT DISTINCT)
-- -----------------------------------------------------------------------------
SELECT 
    m.codigo,
    m.nombre AS Maquina
FROM MAQUINA m
WHERE m.codigo IN (SELECT DISTINCT o.maquina FROM ORDEN_MANTENIMIENTO o)
ORDER BY m.codigo;

-- -----------------------------------------------------------------------------
-- 15. MÁQUINAS SIN NINGUNA ORDEN DE MANTENIMIENTO (SUBCONSULTA CON NOT IN)
-- Ubicación: documentacion-consultas-vistas.md, consulta avanzada CA-15
-- Qué resuelve: Detecta equipos sin historial de mantenimiento (complemento
--               de la CA-14), útil para planear mantenimientos preventivos.
-- Apoya a: sp_resumen_maquina (sp.sql)
-- JOINs / Agregación: MAQUINA + subconsulta NOT IN (SELECT DISTINCT)
-- -----------------------------------------------------------------------------
SELECT 
    m.codigo,
    m.nombre AS Maquina
FROM MAQUINA m
WHERE m.codigo NOT IN (SELECT DISTINCT o.maquina FROM ORDEN_MANTENIMIENTO o);

-- -----------------------------------------------------------------------------
-- 16. LÍNEAS CON FALLAS AÚN SIN RESOLVER (SUBCONSULTA CORRELACIONADA CON EXISTS)
-- Ubicación: documentacion-consultas-vistas.md, consulta avanzada CA-16
-- Qué resuelve: Detecta las líneas que tienen reportes de falla en estado
--               Abierto, En Atención o En Espera.
-- Apoya a: sp_reporte_disponibilidad_planta (sp.sql) y v_kpi_reportes_atencion
-- JOINs / Agregación: LINEA + EXISTS (REPORTE_FALLA JOIN MAQUINA)
-- -----------------------------------------------------------------------------
SELECT 
    l.codigo,
    l.nombre AS Linea
FROM LINEA l
WHERE EXISTS (
    SELECT 1
    FROM REPORTE_FALLA rf
    INNER JOIN MAQUINA m ON m.codigo = rf.maquina
    WHERE m.linea = l.codigo
      AND rf.estado_reporte IN ('ABIER', 'ENATE', 'ENESP')
);

-- -----------------------------------------------------------------------------
-- 17. PROMEDIO DE FALLAS POR LÍNEA (SUBCONSULTA EN FROM / TABLA DERIVADA)
-- Ubicación: documentacion-consultas-vistas.md, consulta avanzada CA-17
-- Qué resuelve: Con una tabla derivada que agrupa el conteo de fallas por
--               máquina, promedia ese conteo a nivel de línea.
-- Apoya a: sp_reporte_disponibilidad_planta (sp.sql)
-- JOINs / Agregación: LINEA LEFT JOIN MAQUINA LEFT JOIN (SELECT ... GROUP BY)
-- -----------------------------------------------------------------------------
SELECT 
    l.nombre AS Linea,
    ROUND(AVG(fc.TotalFallas), 1) AS PromedioFallas
FROM LINEA l
LEFT JOIN MAQUINA m ON m.linea = l.codigo
LEFT JOIN (
    SELECT rf.maquina, COUNT(*) AS TotalFallas
    FROM REPORTE_FALLA rf
    GROUP BY rf.maquina
) fc ON fc.maquina = m.codigo
GROUP BY l.codigo, l.nombre
ORDER BY l.nombre;

-- -----------------------------------------------------------------------------
-- 18. MÁQUINAS CON MTBF SUPERIOR AL PROMEDIO DE SU LÍNEA (SUBCONSULTA
--     CORRELACIONADA ESCALAR EN WHERE)
-- Ubicación: documentacion-consultas-vistas.md, consulta avanzada CA-18
-- Qué resuelve: Compara el MTBF de cada máquina contra el promedio de las
--               máquinas de su propia línea (la subconsulta depende de m.linea).
-- Apoya a: sp_calcular_indicador (sp.sql) y v_kpi_indicadores_actuales
-- JOINs / Agregación: INDICADOR JOIN MAQUINA JOIN LINEA + AVG correlacionado
-- -----------------------------------------------------------------------------
SELECT 
    m.codigo,
    m.nombre AS Maquina,
    i.mtbf AS MTBF,
    l.nombre AS Linea
FROM INDICADOR i
INNER JOIN MAQUINA m ON m.codigo = i.maquina
INNER JOIN LINEA l ON l.codigo = m.linea
WHERE i.mtbf > (
    SELECT AVG(i2.mtbf)
    FROM INDICADOR i2
    INNER JOIN MAQUINA m2 ON m2.codigo = i2.maquina
    WHERE m2.linea = m.linea
)
ORDER BY l.nombre, i.mtbf DESC;

-- -----------------------------------------------------------------------------
-- 19. TÉCNICOS CON MÁS ÓRDENES CERRADAS QUE EL PROMEDIO (SUBCONSULTA EN HAVING)
-- Ubicación: documentacion-consultas-vistas.md, consulta avanzada CA-19
-- Qué resuelve: Filtra el grupo con HAVING comparando contra una subconsulta
--               escalar con AVG sobre una tabla derivada de conteos.
-- Apoya a: sp_rendimiento_trabajador (sp.sql) — mismo ranking que la CA-2
-- JOINs / Agregación: TRABAJADOR LEFT JOIN ORDEN_MANTENIMIENTO + GROUP BY
-- -----------------------------------------------------------------------------
SELECT 
    t.numeroNomina,
    CONCAT(t.nombre, ' ', t.apellidoPat) AS Tecnico,
    COUNT(o.folio) AS OrdenesCerradas
FROM TRABAJADOR t
LEFT JOIN ORDEN_MANTENIMIENTO o
    ON o.trabajador = t.numeroNomina AND o.estado_orden = 'CERRA'
GROUP BY t.numeroNomina, t.nombre, t.apellidoPat
HAVING COUNT(o.folio) > (
    SELECT AVG(cc)
    FROM (
        SELECT COUNT(*) AS cc
        FROM ORDEN_MANTENIMIENTO
        WHERE estado_orden = 'CERRA'
        GROUP BY trabajador
    ) d
);

-- -----------------------------------------------------------------------------
-- 20. MÁQUINAS SIN NINGUNA ORDEN CERRADA (SUBCONSULTA CON NOT EXISTS)
-- Ubicación: documentacion-consultas-vistas.md, consulta avanzada CA-20
-- Qué resuelve: Lista los equipos cuyo mantenimiento no ha sido completado
--               (sin órdenes en estado 'Cerrada').
-- Apoya a: sp_resumen_maquina (sp.sql) y v_kpi_mantenimiento_por_maquina
-- JOINs / Agregación: MAQUINA + NOT EXISTS (ORDEN_MANTENIMIENTO)
-- -----------------------------------------------------------------------------
SELECT 
    m.codigo,
    m.nombre AS Maquina
FROM MAQUINA m
WHERE NOT EXISTS (
    SELECT 1
    FROM ORDEN_MANTENIMIENTO o
    WHERE o.maquina = m.codigo
      AND o.estado_orden = 'CERRA'
);