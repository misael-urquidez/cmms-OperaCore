
-- =====================================================================
-- OperaCore CMMS — PROCEDIMIENTOS ALMACENADOS (módulo de Indicadores/KPI)
-- Requiere: beta4.sql + triggers2.sql ya ejecutados
-- Uso: mysql -u <usuario> -p operacore < procedimientos_almacenados.sql
-- =====================================================================
 
USE operacore;
 
-- =====================================================================
-- Procedimiento 1: sp_cerrar_periodo_indicador
-- =====================================================================
-- Objetivo: cerrar el periodo "vigente" (fechaFin = NULL) de INDICADOR
--           para una máquina y abrir automáticamente el siguiente.
--           Esto es exactamente lo que los triggers de MTBF/MTTR
--           (triggers2.sql) dejaron pendiente a propósito: "Cerrar un
--           periodo es responsabilidad de otro proceso externo al
--           trigger". Este procedimiento ES ese proceso externo.
-- Parámetros:
--   maquinita   -> código de la máquina (MAQUINA.codigo)
--   echa_fin  -> fecha en la que se cierra el periodo actual
-- Lógica:
--   1) Valida que la máquina exista.
--   2) Ubica el periodo abierto de esa máquina (fechaFin IS NULL).
--   3) Valida que la fecha de cierre no sea anterior al inicio.
--   4) Cierra ese periodo (UPDATE fechaFin).
--   5) Abre un periodo nuevo, heredando el último MTBF/MTTR conocido
--      como punto de partida (los triggers lo irán actualizando con
--      los siguientes INSERT en REGISTRO_OPS / cierres de orden).
--   El trigger tg_disponibilidad_indicador_insert (BEFORE INSERT en
--   INDICADOR) recalcula automáticamente porcentajeDispo del nuevo
--   periodo con esos valores heredados — no hace falta repetir esa
--   lógica aquí.
-- =====================================================================

DROP Procedure IF EXISTS sp_cerrar_periodo_indicador;

Delimiter $$


CREATE Procedure sp_cerrar_periodo_indicador(
    in maquinita varchar(10),
    in fecha_fin date
)
begin
    declare existe_maquina int;
    declare id_abierto int;
    declare fecha_inicio date;
    declare mtbf_actual float;
    declare mttr_actual float;

    -- 1) validar que la maquina exista(.-.)
    select count(*) into existe_maquina
    FROM maquina 
    where codigo = maquinita;
    
    IF existe_maquina = 0 then
        signal sqlstate '45000'
        set message_text = "la maquina especifica no existe";
    end if;

    -- 2) ubicar el periodo abierto de la maquina
    select numeroRegistro, fechaInicio, mtbf, mttr
    into id_abierto, fecha_inicio,mtbf_actual, mttr_actual
    from indicador
    where maquina = maquinita and fechaFin IS NULL
    order BY numeroRegistro desc
    LIMIT 1;

    if id_abierto is NULL then
        signal sqlstate '45000'
        set message_text = "No hay un periodo abierto para esta maquina";
    end IF;

    -- 3) validar la fecha de cierre
    IF fecha_fin < fecha_inicio then
        signal sqlstate '45000'
        set message_text = "ka fecga de fin no puede ser anterior al inicio del periodo";
    end if;

    -- 4) cerrar el periodo vigente
    UPDATE indicador
    set fechaFin = fecha_fin
    where numeroRegistro = id_abierto;

    -- 5) abrir el periodo siguiente, heredando el ultimo mtbf,mttr
    INSERT into indicador( maquina,fechaInicio,mtbf,mttr)
    values( maquinita, date_add(fecha_fin, interval 1 DAY), mtbf_actual, mttr_actual);
    end $$

Delimiter ;


 =====================================================================
-- Procedimiento 2: sp_reporte_disponibilidad_planta
-- =====================================================================
-- Objetivo: generar el reporte de disponibilidad/MTBF/MTTR/fallas por
--           LINEA para un rango de fechas arbitrario, elegido por el
--           usuario en el módulo de KPI (ej. "reporte de mayo 2026").
--           Esto NO se puede resolver con una vista simple porque las
--           vistas no aceptan parámetros: v_kpi_disponibilidad_linea
--           te da todo el histórico agrupado por periodo, pero no un
--           corte a la medida por rango de fechas + conteo de fallas y
--           órdenes cerradas en ese mismo rango. Por eso va como SP.
-- Parámetros:
--   fecha_inicio, fecha_fin -> rango del reporte
-- Lógica:
--   1) Valida el rango de fechas.
--   2) Por cada línea, promedia disponibilidad/MTBF/MTTR de los
--      periodos de INDICADOR que se traslapan con el rango pedido.
--   3) Cuenta fallas reportadas y órdenes cerradas de esa línea dentro
--      del mismo rango, como contexto del número.
--   4) Devuelve un result set (una fila por línea) — se consume igual
--      que un SELECT normal desde Django (cursor.callproc + fetchall).
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_reporte_disponibilidad_planta;

DELIMITER $$

CREATE PROCEDURE sp_reporte_disponibilidad_planta(
    IN fecha_inicio DATE,
    IN fecha_fin DATE
)
BEGIN
    -- =========================================================================
    -- PASO 1: VALIDACIÓN DE PARÁMETROS DE ENTRADA
    -- Comprobamos que ninguna fecha venga vacía y que la fecha inicial 
    -- no sea mayor a la final (evita buscar en rangos imposibles).
    -- =========================================================================
    IF fecha_inicio IS NULL OR fecha_fin IS NULL OR fecha_inicio > fecha_fin THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Rango de fechas inválido';
    END IF;

    -- =========================================================================
    -- PASO 2: CONSULTA PRINCIPAL DE INDICADORES POR LÍNEA
    -- =========================================================================
    SELECT
        l.codigo AS linea,
        l.nombre AS nombrelinea,
        
        -- Calculamos el promedio de los indicadores y los redondeamos a 1 decimal.
        -- Como una línea tiene varias máquinas, AVG saca la media del grupo.
        ROUND(AVG(i.porcentajeDispo), 1) AS disponibilidad_promedio,
        ROUND(AVG(i.mtbf), 1) AS mtbf_promedio,
        ROUND(AVG(i.mttr), 1) AS mttr_promedio,
        
        -- ---------------------------------------------------------------------
        -- SUBCONSULTA 1: Conteo de Fallas
        -- Cuenta cuántas fallas ocurrieron en las máquinas de ESTA línea (l.codigo)
        -- dentro del rango de fechas solicitado.
        -- ---------------------------------------------------------------------
        (
            SELECT COUNT(*) 
            FROM reporte_falla AS rf
            -- Unimos con máquina para saber a qué línea pertenece cada falla
            INNER JOIN maquina AS m2 ON m2.codigo = rf.maquina
            WHERE m2.linea = l.codigo
              AND rf.fechaCreacion BETWEEN fecha_inicio AND fecha_fin
        ) AS TotalFallas,

        -- ---------------------------------------------------------------------
        -- SUBCONSULTA 2: Conteo de Órdenes de Mantenimiento Cerradas
        -- Cuenta cuántas órdenes se completaron/cerraron en esta línea
        -- dentro del rango de fechas solicitado.
        -- ---------------------------------------------------------------------
        (
            SELECT COUNT(*) 
            FROM orden_mantenimiento AS om
            -- Unimos con máquina para saber a qué línea pertenece la orden
            INNER JOIN maquina AS m3 ON m3.codigo = om.maquina
            WHERE m3.linea = l.codigo
              AND om.fechacierre BETWEEN fecha_inicio AND fecha_fin
        ) AS OrdenesCerradas

    -- -------------------------------------------------------------------------
    -- UNIÓN DE TABLAS PRINCIPALES (LEFT JOINs)
    -- Usamos LEFT JOIN en lugar de INNER JOIN para asegurarnos de mostrar 
    -- TODAS las líneas de la planta, incluso si alguna no tiene máquinas 
    -- o indicadores registrados aún.
    -- -------------------------------------------------------------------------
    FROM linea AS l
    
    -- 1. Relacionamos la línea con sus máquinas correspondientes
    LEFT JOIN maquina AS m ON m.linea = l.codigo
    
    -- 2. Relacionamos las máquinas con sus registros de indicadores
    LEFT JOIN indicador AS i
           ON i.maquina = m.codigo
           
          -- LÓGICA DE TRASLAPE DE FECHAS:
          -- Solo tomamos los periodos de indicadores que se crucen con el rango
          -- pedido por el usuario:
          -- a) Que el periodo haya iniciado antes (o durante) la fecha final elegida.
          AND i.fechaInicio <= fecha_fin
          -- b) Y que el periodo siga abierto (NULL) o haya terminado después 
          --    (o durante) la fecha inicial elegida.
          AND (i.fechaFin IS NULL OR i.fechaFin >= fecha_inicio)

    -- Agrupamos los resultados por Línea (para que las funciones AVG funcionen por línea)
    GROUP BY l.codigo, l.nombre
    
    -- Ordenamos la lista alfabéticamente por el nombre de la línea
    ORDER BY l.nombre;

END $$

DELIMITER ;

-- =====================================================================
-- Procedimiento 3: sp_registrar_salida_refaccion
-- =====================================================================
-- Objetivo: registrar la salida de una refacción del almacén (cuando
--           un técnico la usa en una reparación) descontando el stock
--           y dejando el registro correspondiente en MOVIMIENTO, de
--           forma atómica. Hoy nada en el sistema hace esto: el stock
--           solo se edita a mano por CRUD y MOVIMIENTO no lo llena
--           ningún endpoint.
-- Parámetros:
--   refaccion    -> REFACCION.numeroRegistro
--   cantidad     -> unidades que se dan de salida
--   orden        -> folio de la orden de mantenimiento (puede ser NULL)
--   descripcioncita  -> texto libre para el movimiento
-- Lógica:
--   1) Valida que la cantidad sea mayor a cero.
--   2) Valida que la refacción exista.
--   3) Valida que haya stock suficiente (nunca deja el stock negativo).
--   4) Descuenta el stock (UPDATE REFACCION).
--   5) Inserta el movimiento en MOVIMIENTO como 'SALIDA'.
--   6) Devuelve el stock resultante y si ya quedó por debajo del
--      stockMinimo, para que la app avise sin consultar aparte.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_registrar_salida_refaccion;

Delimiter $$

CREATE PROCEDURE sp_registrar_salida_refaccion(
    in p_refaccion int,
    in cantidad int,
    in orden varchar(15),
    in descripcioncita varchar(255)
)

BEGIN
    declare stock_Actual int;
    declare stock_minimo int;

    -- 1) validar que la cantidad sea valida
    if cantidad <= 0 THEN
        signal sqlstate '45000'
        set message_text = "la cantidad debe ser mayor a cero";
    end IF;

    -- 2) ubicar la refaccion y su stock actual
    select stock, stockMinimo into stock_Actual, stock_minimo
    from refaccion
    where numeroRegistro = p_refaccion;

    if stock_Actual is NULL then
        signal sqlstate '45000'
        set MESSAGE_TEXT = "La refaccion especificada no existe.";
    end IF;

    -- 3) validar que haya stock suficiente
    if stock_Actual < cantidad then
        signal sqlstate '45000'
        set message_text = "stock insuficiente para esta salida.";
    end IF;

    -- 4) descontar el stock
    UPDATE refaccion
    set stock = stock - cantidad
    where numeroRegistro = p_refaccion;

    -- 5) dejar el registro de auditoria en movimiento
    INSERT into movimiento(descripcion,fecha,hora,tipomovimiento,orden_mantenimiento, refaccion)
    values (descripcioncita, curdate(), curtime(), 'SALIDA', orden, p_refaccion);

    -- 6) informar el resultado a quien llamo el procedimiento
    select (stock_Actual - cantidad) as stock_resultante,
           stock_minimo as stock_minimo_out,
           (stock_Actual - cantidad) <= stock_minimo as requiere_reabastecimiento;

end $$
Delimiter ;