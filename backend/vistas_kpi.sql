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
-- 8. v_kpi_indicadores_actuales: ultimo indicador (MTTR/MTBF/Dispo) por maquina
-- =====================================================================
DROP VIEW IF EXISTS v_kpi_indicadores_actuales;

CREATE VIEW v_kpi_indicadores_actuales as
select m.codigo as Codigo, m.nombre as Maquina, em.nombre as Estado, l.nombre as Linea,
       i.mttr as MTTR, i.mtbf as MTBF, i.porcentajeDispo as Disponibilidad, i.fechaFin as Periodo
from INDICADOR i
inner join MAQUINA m on m.codigo = i.maquina
left join EDO_MAQUINA em on em.codigo = m.estado_maquina
left join LINEA l on l.codigo = m.linea
where i.numeroRegistro = (select max(i2.numeroRegistro) from INDICADOR i2 where i2.maquina = i.maquina);

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
-- FIN DE VISTAS KPI
-- =====================================================================
