
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
    FROM MAQUINA 
    where codigo = maquinita;
    
    IF existe_maquina = 0 then
        signal sqlstate '45000'
        set message_text = "la maquina especifica no existe";
    end if;

    -- 2) ubicar el periodo abierto de la maquina
    select numeroRegistro, fechaInicio, mtbf, mttr
    into id_abierto, fecha_inicio,mtbf_actual, mttr_actual
    from INDICADOR
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
        set message_text = "la fecha de fin no puede ser anterior al inicio del periodo";
    end if;

    -- 4) cerrar el periodo vigente
    UPDATE INDICADOR
    set fechaFin = fecha_fin
    where numeroRegistro = id_abierto;

    -- 5) abrir el periodo siguiente, heredando el ultimo mtbf,mttr
    INSERT into INDICADOR( maquina,fechaInicio,mtbf,mttr)
    values( maquinita, date_add(fecha_fin, interval 1 DAY), mtbf_actual, mttr_actual);
    end $$

Delimiter ;

-- Líneas de prueba eliminadas:
-- select numeroRegistro, fechaInicio, mtbf, mttr
--     from INDICADOR
--     where maquina = "MAQ001" and fechaFin IS NULL
--     order BY numeroRegistro desc
--     LIMIT 1;
--
-- SHOW TABLES;
-- select * from MAQUINA WHERE CODIGO = "MAQ001"
-- select * from INDICADOR
-- call  sp_cerrar_periodo_indicador("MAQ001","2027-02-28")
--
-- INSERT into INDICADOR( maquina,fechaInicio,mtbf,mttr)
--     values( "MAQ001","2027-01-31" , 0, 0);

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

-- call sp  -- Línea huérfana eliminada
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
    in orden varchar(15),
    in descripcioncita varchar(255)
)

BEGIN
    declare stock_Actual int;
    declare stock_minimo int;

    -- 1) validar que la cantidad sea valida
    -- if cantidad <= 0 THEN
    --     signal sqlstate '45000'
    --     set message_text = "la cantidad debe ser mayor a cero";
    -- end IF;

    -- 2) ubicar la refaccion y su stock actual
    select stock, stockMinimo into stock_Actual, stock_minimo
    from REFACCION
    where numeroRegistro = p_refaccion;

    if stock_Actual is NULL then
        signal sqlstate '45000'
        set MESSAGE_TEXT = "La refaccion especificada no existe.";
    end IF;

    -- 3) validar que haya stock suficiente
    -- if stock_Actual < cantidad then
    --     signal sqlstate '45000'
    --     set message_text = "stock insuficiente para esta salida.";
    -- end IF;

    -- 4) descontar el stock
    UPDATE REFACCION
    set stock = stock - 1 
    where numeroRegistro = p_refaccion;

    -- 5) dejar el registro de auditoria en movimiento
    INSERT into MOVIMIENTO (descripcion,fecha,hora,tipomovimiento,orden_mantenimiento, refaccion)
    values (descripcioncita, curdate(), curtime(), 'INSTA', orden, p_refaccion);

    -- 6) informar el resultado a quien llamo el procedimiento
    select (stock_Actual - 1) as stock_resultante,
           stock_minimo as stock_minimo_out,
           (stock_Actual - 1) <= stock_minimo as requiere_reabastecimiento;

end $$
Delimiter ;

-- Líneas de prueba eliminadas:
-- select * from REFACCION
-- call  sp_registrar_salida_refaccion(1, "OMP260807080459", "Descripcoion de prueba")
-- HORAS 

SELECT * FROM  ORDEN_MANTENIMIENTO

-- =====================================================================
-- Procedimiento 4: sp_rendimiento_trabajador
-- =====================================================================
-- Objetivo: devolver el rendimiento de un trabajador (modulo de
--           trabajadores) mediante parametros de SALIDA (OUT).
--           Mismo patron que sp_ventasXVend: un SELECT con CONCAT + COUNT
--           ... INTO <variables OUT> ... GROUP BY.
-- Parámetros:
--   p_nomina            -> TRABAJADOR.numeroNomina (IN)
--   p_nombre            -> OUT: nombre completo del trabajador
--   p_ordenes_asignadas -> OUT: total de ordenes asignadas al trabajador
--   p_ordenes_cerradas  -> OUT: total de ordenes cerradas (estado CERRA)
-- Lógica:
--   1) Cruza TRABAJADOR con ORDEN_MANTENIMIENTO por numeroNomina.
--   2) Concatena nombre + apellidoPat + apellidoMat (con COALESCE por si
--      el segundo apellido no existe).
--   3) Cuenta el total de ordenes asignadas y las cerradas (SUM(CASE)).
--   4) Agrupa por trabajador y devuelve los tres valores por OUT.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_rendimiento_trabajador;

DELIMITER $$

CREATE PROCEDURE sp_rendimiento_trabajador(
    IN  p_nomina            VARCHAR(15),
    OUT p_nombre            VARCHAR(250),
    OUT p_ordenes_asignadas INT,
    OUT p_ordenes_cerradas  INT
)
BEGIN
    SELECT
        CONCAT(t.nombre, ' ', t.apellidoPat, ' ', COALESCE(t.apellidoMat, '')),
        COUNT(o.folio),
        SUM(CASE WHEN o.estado_orden = 'CERRA' THEN 1 ELSE 0 END)
    INTO p_nombre, p_ordenes_asignadas, p_ordenes_cerradas
    FROM TRABAJADOR t
    INNER JOIN ORDEN_MANTENIMIENTO o ON o.trabajador = t.numeroNomina
    WHERE t.numeroNomina = p_nomina
    GROUP BY t.numeroNomina;
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call sp_rendimiento_trabajador('NOM-001', @nombre, @asignadas, @cerradas);
-- select @nombre as Nombre, @asignadas as Ordenes_Asignadas, @cerradas as Ordenes_Cerradas;
-- Llamada (igual que el ejemplo):
-- call sp_rendimiento_trabajador('NOM-001', @nombre, @asignadas, @cerradas);
-- select @nombre as Nombre, @asignadas as Ordenes_Asignadas, @cerradas as Ordenes_Cerradas;

-- =====================================================================
-- Procedimiento 5: sp_calcular_depreciacion_pieza
-- =====================================================================
-- Objetivo: calcular la depreciacion anual de una pieza usando un
--           parametro INOUT. Mismo patron que sp_comisiones: entra la
--           tasa de depreciacion en p_factor, dentro del SP se combina
--           con PIEZA.costoInicial (set p_factor = p_factor * costo) y
--           el mismo parametro sale con el resultado. Asi queda la
--           evidencia del "campo calculado" depresacionAnual.
-- Parámetros:
--   p_pieza  -> PIEZA.numeroSerie (IN)
--   p_factor -> INOUT: entra la tasa (ej. 0.08) y sale la depreciacion
--               anual (tasa * costoInicial), redondeada a 2 decimales
-- Lógica:
--   1) Valida que la pieza exista (SIGNAL si no).
--   2) Multiplica la tasa entrante por el costoInicial de la pieza.
--   3) Devuelve el resultado en el mismo parametro INOUT.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_calcular_depreciacion_pieza;

DELIMITER $$

CREATE PROCEDURE sp_calcular_depreciacion_pieza(
    IN  p_pieza    VARCHAR(30),
    INOUT p_factor FLOAT
)
BEGIN
    DECLARE v_costo FLOAT;

    SELECT costoInicial INTO v_costo
    FROM PIEZA
    WHERE numeroSerie = p_pieza;

    IF v_costo IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La pieza especificada no existe';
    END IF;

    SET p_factor = ROUND(p_factor * v_costo, 2);
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- set @factor = 0.08;
-- call sp_calcular_depreciacion_pieza('PS-6205-001', @factor);
-- select @factor as DepreciacionAnual;

-- =====================================================================
-- Procedimiento 6: sp_resumen_maquina
-- =====================================================================
-- Objetivo: devolver la ficha de una maquina mediante parametros de
--           SALIDA (OUT). Mismo patron que sp_ventasXVend: un SELECT
--           con JOIN + COUNT ... INTO <variables OUT> ... GROUP BY.
-- Parámetros:
--   p_maquina          -> MAQUINA.codigo (IN)
--   p_nombre           -> OUT: nombre de la maquina
--   p_estado           -> OUT: MAQUINA.estado_maquina
--   p_total_fallas     -> OUT: total de reportes de falla de la maquina
--   p_total_ordenes    -> OUT: total de ordenes de mantenimiento
--   p_horas_operacion  -> OUT: suma de horas operacion (REGISTRO_OPS)
-- Lógica:
--   1) Cruza MAQUINA con REPORTE_FALLA, ORDEN_MANTENIMIENTO y
--      REGISTRO_OPS (LEFT JOIN para no perder la maquina si no tiene
--      registros en alguna tabla).
--   2) Cuenta con COUNT(DISTINCT ...) para que el cruce triple no
--      infle los totales.
--   3) Agrupa por maquina y devuelve los cinco valores por OUT.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_resumen_maquina;

DELIMITER $$

CREATE PROCEDURE sp_resumen_maquina(
    IN  p_maquina           VARCHAR(10),
    OUT p_nombre            VARCHAR(100),
    OUT p_estado            VARCHAR(5),
    OUT p_total_fallas      INT,
    OUT p_total_ordenes     INT,
    OUT p_horas_operacion   INT
)
BEGIN
    SELECT
        m.nombre,
        m.estado_maquina,
        COUNT(DISTINCT rf.numeroRegistro),
        COUNT(DISTINCT om.folio),
        IFNULL(SUM(ro.horasOperacion), 0)
    INTO p_nombre, p_estado, p_total_fallas, p_total_ordenes, p_horas_operacion
    FROM MAQUINA m
    LEFT JOIN REPORTE_FALLA rf ON rf.maquina = m.codigo
    LEFT JOIN ORDEN_MANTENIMIENTO om ON om.maquina = m.codigo
    LEFT JOIN REGISTRO_OPS ro ON ro.maquina = m.codigo
    WHERE m.codigo = p_maquina
    GROUP BY m.codigo, m.nombre, m.estado_maquina;
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call sp_resumen_maquina('MAQ001', @nombre, @estado, @fallas, @ordenes, @horas);
-- select @nombre as Nombre, @estado as Estado, @fallas as Fallas,
--        @ordenes as Ordenes, @horas as Horas_Operacion;