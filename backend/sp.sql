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
--   maquinita -> código de la máquina (MAQUINA.codigo)
--   fecha_fin -> fecha en la que se cierra el periodo actual
-- Lógica:
--   1) Valida que la máquina exista.
--   2) Ubica el periodo abierto de esa máquina (fechaFin IS NULL)
--      usando la vista de apoyo v_periodo_abierto_maquina (vistas_kpi.sql).
--   3) Valida que la fecha de cierre no sea anterior al inicio.
--   4) Cierra ese periodo (UPDATE fechaFin).
--   5) Abre un periodo nuevo, heredando el último MTBF/MTTR conocido
--      como punto de partida (los triggers lo irán actualizando con
--      los siguientes INSERT en REGISTRO_OPS / cierres de orden).
--   El trigger tg_disponibilidad_indicador_insert (BEFORE INSERT en
--   INDICADOR) recalcula automáticamente porcentajeDispo del nuevo
--   periodo con esos valores heredados — no hace falta repetir esa
--   lógica aquí.
--   NOTA: el parámetro se llama "maquinita" (y no "maquina") a propósito:
--   v_periodo_abierto_maquina expone una columna llamada "maquina", y un
--   parámetro con el mismo nombre que esa columna queda sombreado por
--   ella en el WHERE (MySQL resuelve el identificador contra la columna,
--   no contra el parámetro), lo que volvía la condición un WHERE maquina
--   = maquina siempre verdadero. Mismo motivo por el que el resto de los
--   SP de este archivo usan prefijo p_ / v_ en sus parámetros y variables.
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_cerrar_periodo_indicador;

DELIMITER $$

CREATE PROCEDURE sp_cerrar_periodo_indicador(
    IN maquinita  VARCHAR(10),
    IN fecha_fin  DATE
)
BEGIN
    DECLARE v_existe_maquina INT;
    DECLARE v_id_abierto     INT;
    DECLARE v_fecha_inicio   DATE;
    DECLARE v_mtbf_actual    FLOAT;
    DECLARE v_mttr_actual    FLOAT;

    SELECT COUNT(*) INTO v_existe_maquina
    FROM MAQUINA
    WHERE codigo = maquinita;

    IF v_existe_maquina = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La maquina especificada no existe';
    END IF;

    SELECT numeroRegistro, fechaInicio, mtbf, mttr
    INTO v_id_abierto, v_fecha_inicio, v_mtbf_actual, v_mttr_actual
    FROM v_periodo_abierto_maquina
    WHERE maquina = maquinita
    ORDER BY numeroRegistro DESC
    LIMIT 1;

    IF v_id_abierto IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No hay un periodo abierto para esta maquina';
    END IF;

    IF fecha_fin < v_fecha_inicio THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La fecha de fin no puede ser anterior al inicio del periodo';
    END IF;

    UPDATE INDICADOR
    SET fechaFin = fecha_fin
    WHERE numeroRegistro = v_id_abierto;

    INSERT INTO INDICADOR (maquina, fechaInicio, mtbf, mttr)
    VALUES (maquinita, DATE_ADD(fecha_fin, INTERVAL 1 DAY), v_mtbf_actual, v_mttr_actual);
END $$

DELIMITER ;
-- Llamada (igual que el ejemplo):
-- call sp_cerrar_periodo_indicador('MAQ001', '2027-02-28');
-- select * from INDICADOR;

-- =====================================================================
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

-- =====================================================================
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
        l.CODIGO AS linea,
        l.NOMBRE AS nombrelinea,

        -- Calculamos el promedio de los indicadores y los redondeamos a 1 decimal.
        -- Como una línea tiene varias máquinas, AVG saca la media del grupo.
        ROUND(AVG(i.porcentajeDispo), 1) AS disponibilidad_promedio,
        ROUND(AVG(i.mtbf), 1) AS mtbf_promedio,
        ROUND(AVG(i.mttr), 1) AS mttr_promedio,

        -- ---------------------------------------------------------------------
        -- SUBCONSULTA 1: Conteo de Fallas
        -- Cuenta cuántas fallas ocurrieron en las máquinas de ESTA línea (l.CODIGO)
        -- dentro del rango de fechas solicitado.
        -- ---------------------------------------------------------------------
        (
            SELECT COUNT(*)
            FROM REPORTE_FALLA AS rf
            -- Unimos con máquina para saber a qué línea pertenece cada falla
            INNER JOIN MAQUINA AS m2 ON m2.CODIGO = rf.maquina
            WHERE m2.LINEA = l.CODIGO
              AND rf.fechaCreacion BETWEEN fecha_inicio AND fecha_fin
        ) AS TotalFallas,

        -- ---------------------------------------------------------------------
        -- SUBCONSULTA 2: Conteo de Órdenes de Mantenimiento Cerradas
        -- Cuenta cuántas órdenes se completaron/cerraron en esta línea
        -- dentro del rango de fechas solicitado.
        -- ---------------------------------------------------------------------
        (
            SELECT COUNT(*)
            FROM ORDEN_MANTENIMIENTO AS om
            -- Unimos con máquina para saber a qué línea pertenece la orden
            INNER JOIN MAQUINA AS m3 ON m3.CODIGO = om.maquina
            WHERE m3.LINEA = l.CODIGO
              AND om.fechacierre BETWEEN fecha_inicio AND fecha_fin
        ) AS OrdenesCerradas

    -- -------------------------------------------------------------------------
    -- UNIÓN DE TABLAS PRINCIPALES (LEFT JOINs)
    -- Usamos LEFT JOIN en lugar de INNER JOIN para asegurarnos de mostrar
    -- TODAS las líneas de la planta, incluso si alguna no tiene máquinas
    -- o indicadores registrados aún.
    -- -------------------------------------------------------------------------
    FROM LINEA AS l

    -- 1. Relacionamos la línea con sus máquinas correspondientes
    LEFT JOIN MAQUINA AS m ON m.LINEA = l.CODIGO

    -- 2. Relacionamos las máquinas con sus registros de indicadores
    LEFT JOIN INDICADOR AS i
           ON i.maquina = m.CODIGO

          -- LÓGICA DE TRASLAPE DE FECHAS:
          -- Solo tomamos los periodos de indicadores que se crucen con el rango
          -- pedido por el usuario:
          -- a) Que el periodo haya iniciado antes (o durante) la fecha final elegida.
          AND i.fechaInicio <= fecha_fin
          -- b) Y que el periodo siga abierto (NULL) o haya terminado después
          --    (o durante) la fecha inicial elegida.
          AND (i.fechaFin IS NULL OR i.fechaFin >= fecha_inicio)

    -- Agrupamos los resultados por Línea (para que las funciones AVG funcionen por línea)
    GROUP BY l.CODIGO, l.NOMBRE

    -- Ordenamos la lista alfabéticamente por el nombre de la línea
    ORDER BY l.NOMBRE;

END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call sp_reporte_disponibilidad_planta('2026-01-01', '2026-06-30');

-- call sp  -- Línea huérfana eliminada
-- =====================================================================
-- Procedimiento 3: sp_registrar_salida_refaccion
-- =====================================================================
-- Objetivo: registrar la salida de una refaccion del almacen (cuando
--           un tecnico la usa en una reparacion) descontando el stock
--           y dejando el registro correspondiente en MOVIMIENTO, de
--           forma atomica. Antes nada en el sistema hacia esto: el
--           stock solo se editaba a mano por CRUD y MOVIMIENTO no lo
--           llenaba ningun endpoint.
-- Parámetros:
--   refaccion    -> REFACCION.numeroRegistro
--   orden        -> folio de la orden de mantenimiento (puede ser NULL)
--   descripcion  -> texto libre para el movimiento
--   fecha        -> fecha del movimiento (si es NULL se usa CURDATE())
--   hora         -> hora del movimiento (si es NULL se usa CURTIME())
--   pieza        -> PIEZA.numeroSerie que se instala (puede ser NULL)
-- Lógica:
--   1) Ubica la refaccion y su stock actual (vista de apoyo
--      v_refaccion_inventario, vistas_kpi.sql).
--   2) Valida que la refaccion exista y que haya stock suficiente.
--   3) Valida la pieza si se indica.
--   4) Descuenta 1 del stock (cada movimiento es de 1 unidad).
--   5) Deja el registro de auditoria en MOVIMIENTO (tipo INSTA) con la
--      fecha/hora indicadas (o las del sistema) y la pieza instalada.
--   6) Devuelve el stock resultante, si quedo por debajo del stockMinimo
--      (para que la app avise sin consultar aparte) y el numeroRegistro
--      del movimiento creado.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_registrar_salida_refaccion;

DELIMITER $$

CREATE PROCEDURE sp_registrar_salida_refaccion(
    IN refaccion    INT,
    IN orden        VARCHAR(15),
    IN descripcion  VARCHAR(255),
    IN fecha        DATE,
    IN hora         TIME,
    IN pieza        VARCHAR(30)
)
BEGIN
    DECLARE v_stock_actual INT;
    DECLARE v_stock_minimo INT;
    DECLARE v_existe_pieza INT;

    -- 1) ubicar la refaccion y su stock actual (vista de apoyo)
    SELECT stock, stockMinimo INTO v_stock_actual, v_stock_minimo
    FROM v_refaccion_inventario
    WHERE numeroRegistro = refaccion;

    -- 2) validar que la refaccion exista
    IF v_stock_actual IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La refaccion especificada no existe';
    END IF;

    -- 2b) validar que haya stock suficiente (hoy el SP podia quedar en 0)
    IF v_stock_actual < 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Stock insuficiente para la salida de refaccion';
    END IF;

    -- 3) validar la pieza si se indica
    IF pieza IS NOT NULL THEN
        SELECT COUNT(*) INTO v_existe_pieza
        FROM PIEZA
        WHERE numeroSerie = pieza;

        IF v_existe_pieza = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La pieza especificada no existe';
        END IF;
    END IF;

    -- 4) descontar el stock (cada movimiento es de 1 unidad)
    UPDATE REFACCION
    SET stock = stock - 1
    WHERE numeroRegistro = refaccion;

    -- 5) dejar el registro de auditoria en MOVIMIENTO (tipo INSTA) con la
    --    fecha/hora indicadas (o las del sistema) y la pieza instalada.
    INSERT INTO MOVIMIENTO (descripcion, fecha, hora, tipoMovimiento, orden_mantenimiento, refaccion, PIEZA)
    VALUES (descripcion, COALESCE(fecha, CURDATE()), COALESCE(hora, CURTIME()), 'INSTA', orden, refaccion, pieza);

    -- 6) informar el resultado a quien llamo el procedimiento
    SELECT (v_stock_actual - 1) AS stock_resultante,
           v_stock_minimo AS stock_minimo_out,
           (v_stock_actual - 1) <= v_stock_minimo AS requiere_reabastecimiento,
           LAST_INSERT_ID() AS numero_movimiento;
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call sp_registrar_salida_refaccion(1, 'OMP260807080459', 'Descripcion de prueba', '2026-08-08', '10:30:00', 'SN123456');
-- select * from REFACCION;
-- Líneas de prueba eliminadas:
-- select * from REFACCION
-- call  sregistrar_salida_refaccion(1, "OMP260807080459", "Descripcoion de prueba")
-- HORAS 

-- SELECT * FROM  ORDEN_MANTENIMIENTO  -- Consulta de prueba temporal (eliminada)

-- =====================================================================
-- Procedimiento 4: srendimiento_trabajador
-- =====================================================================
-- Objetivo: devolver el rendimiento de un trabajador (modulo de
--           trabajadores) mediante parametros de SALIDA (OUT).
--           Mismo patron que sventasXVend: un SELECT con CONCAT + COUNT
--           ... INTO <variables OUT> ... GROUP BY.
-- Parámetros:
--   nomina            -> TRABAJADOR.numeroNomina (IN)
--   nombre            -> OUT: nombre completo del trabajador
--   ordenes_asignadas -> OUT: total de ordenes asignadas al trabajador
--   ordenes_cerradas  -> OUT: total de ordenes cerradas (estado CERRA)
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
    IN  nomina            VARCHAR(15),
    OUT nombre            VARCHAR(250),
    OUT ordenes_asignadas INT,
    OUT ordenes_cerradas  INT
)
BEGIN
    SELECT
        CONCAT(t.nombre, ' ', t.apellidoPat, ' ', COALESCE(t.apellidoMat, '')),
        COUNT(o.folio),
        SUM(CASE WHEN o.estado_orden = 'CERRA' THEN 1 ELSE 0 END)
    INTO nombre, ordenes_asignadas, ordenes_cerradas
    FROM TRABAJADOR t
    INNER JOIN ORDEN_MANTENIMIENTO o ON o.trabajador = t.numeroNomina
    WHERE t.numeroNomina = nomina
    GROUP BY t.numeroNomina;
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call srendimiento_trabajador('NOM-001', @nombre, @asignadas, @cerradas);
-- select @nombre as Nombre, @asignadas as Ordenes_Asignadas, @cerradas as Ordenes_Cerradas;
-- Llamada (igual que el ejemplo):
-- call srendimiento_trabajador('NOM-001', @nombre, @asignadas, @cerradas);
-- select @nombre as Nombre, @asignadas as Ordenes_Asignadas, @cerradas as Ordenes_Cerradas;

-- =====================================================================
-- Procedimiento 5: scalcular_depreciacion_pieza
-- =====================================================================
-- Objetivo: calcular la depreciacion anual de una pieza usando un
--           parametro INOUT. Mismo patron que scomisiones: entra la
--           tasa de depreciacion en factor, dentro del SP se combina
--           con PIEZA.costoInicial (set factor = factor * costo) y
--           el mismo parametro sale con el resultado. Asi queda la
--           evidencia del "campo calculado" depresacionAnual.
-- Parámetros:
--   pieza  -> PIEZA.numeroSerie (IN)
--   factor -> INOUT: entra la tasa (ej. 0.08) y sale la depreciacion
--               anual (tasa * costoInicial), redondeada a 2 decimales
-- Lógica:
--   1) Valida que la pieza exista (SIGNAL si no).
--   2) Multiplica la tasa entrante por el costoInicial de la pieza.
--   3) Devuelve el resultado en el mismo parametro INOUT.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_calcular_depreciacion_pieza;

DELIMITER $$

CREATE PROCEDURE sp_calcular_depreciacion_pieza(
    IN  pieza    VARCHAR(30),
    INOUT factor FLOAT
)
BEGIN
    DECLARE v_costo FLOAT;

    SELECT costoInicial INTO v_costo
    FROM PIEZA
    WHERE numeroSerie = pieza;

    IF v_costo IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La pieza especificada no existe';
    END IF;

    SET factor = ROUND(factor * v_costo, 2);
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- set @factor = 0.08;
-- call sp_calcular_depreciacion_pieza('PS-6205-001', @factor);
-- select @factor as DepreciacionAnual;

-- =====================================================================
-- Procedimiento 6a: sp_resumen_maquina_maquinaria (antes sp_resumen_maquina,
--                    version de Misael)
-- =====================================================================
-- NOTA DE MERGE: Misael y Luis crearon cada quien un sp_resumen_maquina
-- distinto para modulos distintos (maquinaria vs monitoreo). Para no
-- pisar ninguno de los dos, esta version (la de Misael, usada por
-- api/apps/maquinaria/views.py) se renombro a sp_resumen_maquina_maquinaria.
-- La version de Luis (usada por monitoreo) se quedo con el nombre
-- original sp_resumen_maquina. Pendiente: decidir si a la larga se
-- unifica en una sola.
-- Objetivo: devolver la ficha resumen de una máquina (nombre, estado, total de fallas,
--           total de órdenes de mantenimiento, horas de operación acumuladas,
--           e indicadores vigentes: mtbf, mttr, % disponibilidad).
-- Parámetros:
--   p_maquina          -> MAQUINA.codigo (IN)
--   p_nombre           -> OUT: nombre de la máquina
--   p_estado           -> OUT: MAQUINA.estado_maquina
--   p_total_fallas     -> OUT: total de reportes de falla de la máquina
--   p_total_ordenes    -> OUT: total de órdenes de mantenimiento
--   p_horas_operacion  -> OUT: suma de horas operación (REGISTRO_OPS)
--   p_mtbf             -> OUT: MTBF vigente
--   p_mttr             -> OUT: MTTR vigente
--   p_disponibilidad   -> OUT: % disponibilidad vigente
-- Lógica:
--   1) Cruza MAQUINA con REPORTE_FALLA, ORDEN_MANTENIMIENTO y REGISTRO_OPS
--      (LEFT JOIN para no perder la máquina si no tiene registros).
--   2) Cuenta con COUNT(DISTINCT ...) para que el cruce triple no infle los totales.
--   3) Agrupa por máquina y devuelve los valores básicos por OUT.
--   4) Para los indicadores (MTBF, MTTR, disponibilidad), prioriza el periodo
--      abierto (fechaFin IS NULL); si no hay uno abierto, usa el último periodo
--      cerrado como respaldo.
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_resumen_maquina_maquinaria;

DELIMITER $$

CREATE PROCEDURE sp_resumen_maquina_maquinaria(
    IN  p_maquina           VARCHAR(10),
    OUT p_nombre            VARCHAR(100),
    OUT p_estado            VARCHAR(5),
    OUT p_total_fallas      INT,
    OUT p_total_ordenes     INT,
    OUT p_horas_operacion   INT,
    OUT p_mtbf              FLOAT,
    OUT p_mttr              FLOAT,
    OUT p_disponibilidad    INT
)
BEGIN
    SELECT
        m.nombre,
        m.estado_maquina,
        COUNT(DISTINCT rf.numeroRegistro),
        COUNT(DISTINCT om.folio),
        (
            SELECT IFNULL(SUM(ro.horasOperacion), 0)
            FROM REGISTRO_OPS ro
            WHERE ro.maquina = m.codigo
        )
    INTO p_nombre, p_estado, p_total_fallas, p_total_ordenes, p_horas_operacion
    FROM MAQUINA m
    LEFT JOIN REPORTE_FALLA rf ON rf.maquina = m.codigo
    LEFT JOIN ORDEN_MANTENIMIENTO om ON om.maquina = m.codigo
    WHERE m.codigo = p_maquina
    GROUP BY m.codigo, m.nombre, m.estado_maquina;

    -- Indicadores vigentes: prioriza el periodo abierto (fechaFin IS NULL);
    -- si no hay uno abierto, cae al ultimo periodo cerrado como respaldo.
    SELECT i.mtbf, i.mttr, i.porcentajeDispo
    INTO p_mtbf, p_mttr, p_disponibilidad
    FROM INDICADOR i
    WHERE i.maquina = p_maquina
    ORDER BY (i.fechaFin IS NULL) DESC, i.numeroRegistro DESC
    LIMIT 1;
END $$

DELIMITER ;

-- Llamada:
-- call sp_resumen_maquina_maquinaria('MAQ001', @nombre, @estado, @fallas, @ordenes, @horas, @mtbf, @mttr, @dispo);
-- select @nombre, @estado, @fallas, @ordenes, @horas, @mtbf, @mttr, @dispo;

-- =====================================================================
-- Procedimiento 6b: sp_resumen_maquina (version de Luis, para Monitoreo)
-- =====================================================================
-- Objetivo: devolver la ficha de indicadores de una maquina mediante
--           parametros de SALIDA (OUT). Es la pieza que el modulo de
--           Monitoreo usa para el drawer de maquina: el endpoint
--           GET /api/monitoreo/maquinas/<codigo>/indicadores/ (vista
--           IndicadoresMaquinaAPIView, api/apps/monitoreo/views.py)
--           llama a este SP y mapea los OUT al JSON que pinta el panel
--           lateral (client/templates/monitoreo/index.html).
--           Sustituye la lectura directa por ORM de IndicadorActual:
--           ahora toda la ficha sale de un unico SP con parametros OUT.
-- Parámetros:
--   maquina            -> MAQUINA.codigo (IN)
--   nombre             -> OUT: nombre de la maquina
--   estado             -> OUT: EDO_MAQUINA.nombre (estado de la maquina)
--   mtbf               -> OUT: MTBF (horas) del ultimo periodo
--   mttr               -> OUT: MTTR (horas) del ultimo periodo
--   disponibilidad     -> OUT: % de disponibilidad del ultimo periodo
--   total_horas        -> OUT: SUM(REGISTRO_OPS.horasOperacion)
--   numero_fallas      -> OUT: COUNT(REPORTE_FALLA)
--   tiempo_inactividad -> OUT: SUM(REPORTE_FALLA.tiempoParo) de fallas
--                                  con orden cerrada
--   numero_reparaciones-> OUT: COUNT de ordenes cerradas con reporte
--                                  de falla
-- Lógica:
--   1) Lee la ficha desde la vista de apoyo v_kpi_indicadores_actuales
--      (vistas_kpi.sql), que entrega el ultimo periodo de INDICADOR por
--      maquina (subconsulta correlacionada MAX, consulta avanzada CA-13)
--      mas las tablas derivadas de horas de operacion, fallas, tiempo
--      de paro y reparaciones calculadas en vivo.
--   2) Mapea cada columna de la vista a un parametro OUT con SELECT INTO.
--      Si la maquina no tiene indicadores todavia, la vista no devuelve
--      fila y los OUT quedan en NULL (el endpoint los convierte en 0).
--   Patron: SP que consume una vista de apoyo (igual que el SP1 con
--   v_periodo_abierto_maquina y el SP3 con v_refaccion_inventario).
-- =====================================================================

DROP PROCEDURE IF EXISTS sp_resumen_maquina;

DELIMITER $$

CREATE PROCEDURE sp_resumen_maquina(
    IN  p_maquina             VARCHAR(10),
    OUT p_nombre              VARCHAR(100),
    OUT p_estado              VARCHAR(50),
    OUT p_mtbf                FLOAT,
    OUT p_mttr                FLOAT,
    OUT p_disponibilidad      INT,
    OUT p_total_horas         INT,
    OUT p_numero_fallas       INT,
    OUT p_tiempo_inactividad  INT,
    OUT p_numero_reparaciones INT
)
BEGIN
    SELECT
        Maquina,
        Estado,
        MTTR,
        MTBF,
        Disponibilidad,
        TotalHorasOperacion,
        TotalFallas,
        TiempoTotalParo,
        NumReparaciones
    INTO
        p_nombre,
        p_estado,
        p_mttr,
        p_mtbf,
        p_disponibilidad,
        p_total_horas,
        p_numero_fallas,
        p_tiempo_inactividad,
        p_numero_reparaciones
    FROM v_kpi_indicadores_actuales
    WHERE Codigo = p_maquina;
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call sp_resumen_maquina('MAQ001', @nombre, @estado, @mtbf, @mttr, @dispo,
--                         @horas, @fallas, @inactividad, @reparaciones);
-- select @nombre, @estado, @mtbf, @mttr, @dispo,
--        @horas, @fallas, @inactividad, @reparaciones;

-- =====================================================================
-- Procedimiento 7: sp_historial_maquina
-- =====================================================================
-- Objetivo: devolver, en un solo result set, todas las ordenes de
--           mantenimiento y todos los reportes de falla de una maquina,
--           con el trabajador que atendio cada uno. Va como result set
--           (no OUT) porque es una lista de N filas, no un escalar.
-- Parámetros:
--   p_maquina -> MAQUINA.codigo
-- Lógica:
--   1) UNION ALL entre ORDEN_MANTENIMIENTO y REPORTE_FALLA, marcando el
--      tipo de cada fila ('ORDEN' / 'FALLA').
--   2) LEFT JOIN con TRABAJADOR para traer el nombre completo de quien
--      la atendio (LEFT porque trabajador puede ser NULL en ordenes).
--   3) Ordena todo por fecha descendente (mas reciente primero).
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_historial_maquina;

DELIMITER $$

CREATE PROCEDURE sp_historial_maquina(
    IN p_maquina VARCHAR(10)
)
BEGIN
    SELECT
        'ORDEN' AS tipo,
        om.folio AS identificador,
        om.fechaCreacion AS fecha,
        om.descripcion AS detalle,
        om.estado_orden AS estado,
        om.trabajador AS trabajador_nomina,
        CONCAT(t.nombre, ' ', t.apellidoPat, ' ', COALESCE(t.apellidoMat, '')) AS trabajador_nombre
    FROM ORDEN_MANTENIMIENTO om
    LEFT JOIN TRABAJADOR t ON t.numeroNomina = om.trabajador
    WHERE om.maquina = p_maquina

    UNION ALL

    SELECT
        'FALLA' AS tipo,
        CAST(rf.numeroRegistro AS CHAR) AS identificador,
        rf.fechaCreacion AS fecha,
        rf.asunto AS detalle,
        rf.estado_reporte AS estado,
        rf.trabajador AS trabajador_nomina,
        CONCAT(t.nombre, ' ', t.apellidoPat, ' ', COALESCE(t.apellidoMat, '')) AS trabajador_nombre
    FROM REPORTE_FALLA rf
    LEFT JOIN TRABAJADOR t ON t.numeroNomina = rf.trabajador
    WHERE rf.maquina = p_maquina

    ORDER BY fecha DESC;
END $$

DELIMITER ;

-- Llamada:
-- call sp_historial_maquina('MAQ001');