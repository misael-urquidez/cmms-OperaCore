-- =====================================================================
-- OperaCore CMMS — VISTAS KPI PARA EL PANEL DE INDICADORES
-- Panel objetivo: client/templates/indicadores/index.html (borrador)
--
-- Uso: mysql -u <usuario> -p operacore < vistas_kpi.sql
-- Requiere primero: beta4.sql + triggers2.sql
--
-- Mapeo con la pantalla:
--   v_kpi_estado_flota            -> doughnut + tarjetas de estado
--   v_kpi_reportes_atencion       -> tarjetas (fallas abiertas, ordenes activas)
--   v_kpi_stock                   -> tarjeta y tabla de refacciones bajo stock
--   v_kpi_fallas_por_maquina      -> Pareto (top maquinas con mas fallas)
--   v_kpi_top_fallas              -> top tipos de falla
--   v_kpi_horas_operacion         -> horas operadas por maquina
--   v_kpi_mantenimiento_por_maquina -> preventivo vs correctivo por linea
--   v_kpi_indicadores_actuales    -> tabla MTTR/MTBF/Disponibilidad
--   v_kpi_disponibilidad_linea    -> linea de disponibilidad por periodo
--   v_kpi_monitoreo_predictivo    -> ultima lectura de sensor por maquina
--   v_periodo_abierto_maquina     -> apoyo a sp_cerrar_periodo_indicador (sp.sql)
--   v_refaccion_inventario        -> apoyo a sp_registrar_salida_refaccion (sp.sql);
--                                    base de v_kpi_stock
-- =====================================================================

USE operacore;

-- =====================================================================
-- 1. v_kpi_estado_flota: distribucion actual de la flota por estado
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_estado_flota;

CREATE VIEW v_kpi_estado_flota as
select em.nombre as Estado, count(*) as Total
from MAQUINA m
inner join EDO_MAQUINA em on em.codigo = m.estado_maquina
group by em.nombre
order by Total desc;

-- =====================================================================
-- 2. v_kpi_reportes_atencion: fallas abiertas y ordenes activas
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_reportes_atencion;

CREATE VIEW v_kpi_reportes_atencion as
select
  (select count(*) from REPORTE_FALLA where estado_reporte in ('ABIER','ENATE','ENESP')) as FallasAbiertas,
  (select count(*) from ORDEN_MANTENIMIENTO where estado_orden not in ('CERRA','CANCE')) as OrdenesActivas,
  (select count(*) from ORDEN_MANTENIMIENTO where estado_orden = 'ENPRO') as OrdenesEnProgreso;

-- =====================================================================
-- 3. v_kpi_stock: refacciones por debajo o igual al stock minimo
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_stock;

CREATE VIEW v_kpi_stock as
select r.nombre as Refaccion, r.codigoSku as SKU,
       r.stock as Stock, r.stockMinimo as StockMinimo,
       (r.stockMinimo - r.stock) as Faltantes,
       c.nombre as Criticidad
from REFACCION r
left join CLASIFICACION c on c.codigo = r.clasificacion
where r.stock <= r.stockMinimo
order by Faltantes desc;

-- =====================================================================
-- 4. v_kpi_fallas_por_maquina: conteo de reportes de falla por maquina
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_fallas_por_maquina;

CREATE VIEW v_kpi_fallas_por_maquina as
select m.codigo as Codigo, m.nombre as Maquina, count(r.numeroRegistro) as TotalFallas
from MAQUINA m
left join REPORTE_FALLA r on r.maquina = m.codigo
group by m.codigo, m.nombre
order by TotalFallas desc;

-- =====================================================================
-- 5. v_kpi_top_fallas: tipos de falla mas frecuentes
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_top_fallas;

CREATE VIEW v_kpi_top_fallas as
select tf.nombre as TipoFalla, count(tr.reporte_falla) as Total
from TIPO_FALLA tf
left join TIPO_REPORTE tr on tr.tipo_falla = tf.numeroRegistro
group by tf.numeroRegistro, tf.nombre
order by Total desc;

-- =====================================================================
-- 6. v_kpi_horas_operacion: horas totales operadas por maquina
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_horas_operacion;

CREATE VIEW v_kpi_horas_operacion as
select m.codigo as Codigo, m.nombre as Maquina, sum(ro.horasOperacion) as HorasOperacion
from MAQUINA m
left join REGISTRO_OPS ro on ro.maquina = m.codigo
group by m.codigo, m.nombre
order by HorasOperacion desc;

-- =====================================================================
-- 7. v_kpi_mantenimiento_por_maquina: preventivo vs correctivo por linea
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_mantenimiento_por_maquina;

CREATE VIEW v_kpi_mantenimiento_por_maquina as
select l.nombre as Linea,
       sum(case when o.tipo_mantenimiento = 'PREVE' then 1 else 0 end) as Preventivos,
       sum(case when o.tipo_mantenimiento in ('CORRE','EMER') then 1 else 0 end) as Correctivos,
       count(o.folio) as Total
from ORDEN_MANTENIMIENTO o
left join MAQUINA m on m.codigo = o.maquina
left join LINEA l on l.codigo = m.linea
group by l.codigo, l.nombre
order by l.nombre;

-- =====================================================================
-- 8. v_kpi_indicadores_actuales: ficha KPI por maquina (MAQUINA-céntrica).
--    Base: MAQUINA con LEFT JOINs para que aparezcan TODAS las maquinas,
--    incluso sin indicadores registrados. Incluye los datos de origen de
--    las fórmulas, calculados en vivo (misma lógica que los triggers de
--    triggers2.sql) mas el total de ordenes:
--      EstadoCodigo        -> MAQUINA.estado_maquina (codigo, ej. OPERA)
--      TotalHorasOperacion -> SUM(REGISTRO_OPS.horasOperacion)
--      TotalFallas         -> COUNT(REPORTE_FALLA)
--      TotalOrdenes        -> COUNT(ORDEN_MANTENIMIENTO) (todas)
--      TiempoTotalParo     -> SUM(REPORTE_FALLA.tiempoParo) de fallas con
--                             orden cerrada (alimenta MTTR)
--      NumReparaciones     -> COUNT de órdenes cerradas con reporte de falla
--    La consume sp_resumen_maquina (sp.sql) y el módulo KPI
--    (endpoint v1/kpi/indicadores-actuales/, dashboard.js).
-- =====================================================================
/* ---------------------------------------------------------------------
   VERSIÓN ANTERIOR (solo referencia; quedaba INDICADOR-céntrica y no
   traía total de ordenes). Rebasada a MAQUINA-céntrica para que
   sp_resumen_maquina sirva a maquinas sin indicadores.
   ---------------------------------------------------------------------
   select m.codigo as Codigo, m.nombre as Maquina, em.nombre as Estado, l.nombre as Linea,
          i.mttr as MTTR, i.mtbf as MTBF, i.porcentajeDispo as Disponibilidad, i.fechaFin as Periodo,
          IFNULL(ro.TotalHoras, 0)      as TotalHorasOperacion,
          IFNULL(rf.TotalFallas, 0)     as TotalFallas,
          IFNULL(om.TiempoParo, 0)      as TiempoTotalParo,
          IFNULL(om.NumReparaciones, 0) as NumReparaciones
   from INDICADOR i
   inner join MAQUINA m on m.codigo = i.maquina
   left join EDO_MAQUINA em on em.codigo = m.estado_maquina
   left join LINEA l on l.codigo = m.linea
   left join ( select maquina, SUM(horasOperacion) as TotalHoras from REGISTRO_OPS group by maquina ) ro on ro.maquina = m.codigo
   left join ( select maquina, COUNT(*) as TotalFallas from REPORTE_FALLA group by maquina ) rf on rf.maquina = m.codigo
   left join ( select om.maquina, SUM(rf2.tiempoParo) as TiempoParo, COUNT(*) as NumReparaciones
               from ORDEN_MANTENIMIENTO om
               inner join REPORTE_FALLA rf2 on rf2.numeroRegistro = om.reporte_falla
               where om.fechaCierre is not null
               group by om.maquina ) om on om.maquina = m.codigo
   where i.numeroRegistro = (select max(i2.numeroRegistro) from INDICADOR i2 where i2.maquina = i.maquina);
   --------------------------------------------------------------------- */
DROP VIEW IF EXISTS v_kpi_indicadores_actuales;

CREATE VIEW v_kpi_indicadores_actuales as
select m.codigo as Codigo, m.nombre as Maquina, em.nombre as Estado,
       m.estado_maquina as EstadoCodigo, l.nombre as Linea,
       i.mttr as MTTR, i.mtbf as MTBF, i.porcentajeDispo as Disponibilidad, i.fechaFin as Periodo,
       IFNULL(ro.TotalHoras, 0)       as TotalHorasOperacion,
       IFNULL(rf.TotalFallas, 0)      as TotalFallas,
       IFNULL(om_tot.TotalOrdenes, 0) as TotalOrdenes,
       IFNULL(om.TiempoParo, 0)       as TiempoTotalParo,
       IFNULL(om.NumReparaciones, 0)  as NumReparaciones
from MAQUINA m
left join EDO_MAQUINA em on em.codigo = m.estado_maquina
left join LINEA l on l.codigo = m.linea
left join (
    select i2.maquina, i2.mttr, i2.mtbf, i2.porcentajeDispo, i2.fechaFin
    from INDICADOR i2
    inner join (
        select maquina, MAX(numeroRegistro) as maxreg
        from INDICADOR
        group by maquina
    ) ult on ult.maquina = i2.maquina and ult.maxreg = i2.numeroRegistro
) i on i.maquina = m.codigo
left join (
    select maquina, SUM(horasOperacion) as TotalHoras
    from REGISTRO_OPS
    group by maquina
) ro on ro.maquina = m.codigo
left join (
    select maquina, COUNT(*) as TotalFallas
    from REPORTE_FALLA
    group by maquina
) rf on rf.maquina = m.codigo
left join (
    select maquina, COUNT(*) as TotalOrdenes
    from ORDEN_MANTENIMIENTO
    group by maquina
) om_tot on om_tot.maquina = m.codigo
left join (
    select om.maquina,
           SUM(rf2.tiempoParo) as TiempoParo,
           COUNT(*)            as NumReparaciones
    from ORDEN_MANTENIMIENTO om
    inner join REPORTE_FALLA rf2 on rf2.numeroRegistro = om.reporte_falla
    where om.fechaCierre is not null
    group by om.maquina
) om on om.maquina = m.codigo;

-- =====================================================================
-- 9. v_kpi_disponibilidad_linea: disponibilidad promedio por linea y periodo
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_disponibilidad_linea;

CREATE VIEW v_kpi_disponibilidad_linea as
select l.nombre as Linea, i.fechaFin as Periodo,
       round(avg(i.porcentajeDispo), 1) as Disponibilidad
from INDICADOR i
inner join MAQUINA m on m.codigo = i.maquina
inner join LINEA l on l.codigo = m.linea
group by l.codigo, l.nombre, i.fechaFin
order by l.nombre, i.fechaFin;

-- =====================================================================
-- 10. v_kpi_monitoreo_predictivo: ultima lectura de sensor por maquina
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_monitoreo_predictivo;

CREATE VIEW v_kpi_monitoreo_predictivo as
select m.codigo as Codigo, m.nombre as Maquina, m.umbral_vibracion as Umbral,
       s.vibracion as Vibracion, s.temperatura as Temperatura, s.timestamp as Fecha,
       case when s.vibracion > m.umbral_vibracion then 1 else 0 end as Excede
from LECTURA_SENSOR s
inner join MAQUINA m on m.codigo = s.maquina
where s.numeroRegistro = (select max(s2.numeroRegistro) from LECTURA_SENSOR s2 where s2.maquina = s.maquina);

-- =====================================================================
-- 11. v_periodo_abierto_maquina: periodos vigentes (fechaFin NULL)
--     Vista de apoyo consumida por sp_cerrar_periodo_indicador (sp.sql):
--     encapsula el concepto de "periodo vigente" que el SP necesita
--     localizar para cerrar y abrir el siguiente.
-- =====================================================================
DROP VIEW IF EXISTS v_periodo_abierto_maquina;

CREATE VIEW v_periodo_abierto_maquina as
select numeroRegistro, maquina, fechaInicio, mtbf, mttr
from INDICADOR
where fechaFin IS NULL;

-- =====================================================================
-- 12. v_refaccion_inventario: catalogo de refacciones con su stock
--     Stock total (REFACCION.stock), que es la suma de las cantidades
--     por estado en ESTADO_REFACCION (mantenida por los triggers de
--     triggers2.sql). v_kpi_stock es un filtro de esta vista (solo
--     refacciones en/bajo el stock minimo).
-- =====================================================================
DROP VIEW IF EXISTS v_refaccion_inventario;

CREATE VIEW v_refaccion_inventario as
select r.numeroRegistro, r.nombre, r.codigoSku, r.stock, r.stockMinimo,
       r.costo, r.puntoReorden, c.nombre as clasificacion
from REFACCION r
left join CLASIFICACION c on c.codigo = r.clasificacion;

-- =====================================================================
-- FIN DE VISTAS KPI
-- =====================================================================


VISTA DONDE MUESTRE ESTADOS 