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

-- DOCUMENTADO

DROP PROCEDURE IF EXISTS sp_cerrar_periodo_indicador;

DELIMITER $$

CREATE PROCEDURE sp_cerrar_periodo_indicador(
    IN maquinita  VARCHAR(10),
    IN fecha_fin  DATE
)
BEGIN
    DECLARE existe_maquina INT;
    DECLARE id_abierto     INT;
    DECLARE fecha_inicio   DATE;
    DECLARE mtbf_actual    FLOAT;
    DECLARE mttr_actual    FLOAT;

    -- 1) validar que la maquina exista
    SELECT COUNT(*) INTO existe_maquina
    FROM MAQUINA
    WHERE codigo = maquinita;

    IF existe_maquina = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La maquina especificada no existe';
    END IF;

    -- 2) ubicar el periodo abierto de la maquina (vista de apoyo).
    --    La columna se califica con el alias vp A PROPOSITO: en MySQL,
    --    dentro de un SP un nombre sin calificar que coincida con un
    --    parametro/variable resuelve a la VARIABLE, no a la columna
    --    (refman: local-variable-scope). Sin el alias, la consulta
    --    'maquina = (SELECT maquina)' quedaria 'param = param'
    --    (siempre true) y tomaria el periodo de cualquier maquina.
    SELECT vp.numeroRegistro, vp.fechaInicio, vp.mtbf, vp.mttr
    INTO id_abierto, fecha_inicio, mtbf_actual, mttr_actual
    FROM v_periodo_abierto_maquina AS vp
    WHERE vp.maquina = maquina
    ORDER BY vp.numeroRegistro DESC
    LIMIT 1;

    IF id_abierto IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No hay un periodo abierto para esta maquina';
    END IF;

    -- 3) validar la fecha de cierre
    IF fecha_fin < fecha_inicio THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La fecha de fin no puede ser anterior al inicio del periodo';
    END IF;

    UPDATE INDICADOR
    SET fechaFin = fecha_fin
    WHERE numeroRegistro = id_abierto;

    INSERT INTO INDICADOR (maquina, fechaInicio, mtbf, mttr)
    VALUES (maquina, DATE_ADD(fecha_fin, INTERVAL 1 DAY), mtbf_actual, mttr_actual);
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
-- Procedimiento 2: sp_reporte_disponibilidad_linea
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

-- DOCUMENTADO

DROP PROCEDURE IF EXISTS sp_reporte_disponibilidad_linea;
-- Migracion: elimina el procedimiento con el nombre anterior (se renombro
-- de sp_reporte_disponibilidad_planta a sp_reporte_disponibilidad_linea).
DROP PROCEDURE IF EXISTS sp_reporte_disponibilidad_planta;

DELIMITER $$

CREATE PROCEDURE sp_reporte_disponibilidad_linea(
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


        (
            SELECT ROUND(AVG(i.porcentajeDispo), 1)
            FROM INDICADOR AS i
            INNER JOIN MAQUINA AS m ON m.codigo = i.maquina
            WHERE m.linea = l.CODIGO
              AND i.fechaInicio <= fecha_fin
              AND (i.fechaFin IS NULL OR i.fechaFin >= fecha_inicio)
        ) AS disponibilidad_promedio,

        (
            SELECT ROUND(AVG(i.mtbf), 1)
            FROM INDICADOR AS i
            INNER JOIN MAQUINA AS m ON m.codigo = i.maquina
            WHERE m.linea = l.CODIGO
              AND i.fechaInicio <= fecha_fin
              AND (i.fechaFin IS NULL OR i.fechaFin >= fecha_inicio)
        ) AS mtbf_promedio,

        (
            SELECT ROUND(AVG(i.mttr), 1)
            FROM INDICADOR AS i
            INNER JOIN MAQUINA AS m ON m.codigo = i.maquina
            WHERE m.linea = l.CODIGO
              AND i.fechaInicio <= fecha_fin
              AND (i.fechaFin IS NULL OR i.fechaFin >= fecha_inicio)
        ) AS mttr_promedio,


        (
            SELECT COUNT(*)
            FROM REPORTE_FALLA AS rf
            -- Unimos con máquina para saber a qué línea pertenece cada falla
            INNER JOIN MAQUINA AS m2 ON m2.CODIGO = rf.maquina
            WHERE m2.LINEA = l.CODIGO
              AND rf.fechaCreacion BETWEEN fecha_inicio AND fecha_fin
        ) AS TotalFallas,


        (
            SELECT COUNT(*)
            FROM ORDEN_MANTENIMIENTO AS om
            -- Unimos con máquina para saber a qué línea pertenece la orden
            INNER JOIN MAQUINA AS m3 ON m3.CODIGO = om.maquina
            WHERE m3.LINEA = l.CODIGO
              AND om.fechacierre BETWEEN fecha_inicio AND fecha_fin
        ) AS OrdenesCerradas

    -- Una fila por línea; los agregados ya son subconsultas escalares, asi
    -- que no hace falta GROUP BY.
    FROM LINEA AS l

    -- Ordenamos la lista alfabéticamente por el nombre de la línea
    ORDER BY l.NOMBRE;

END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call sp_reporte_disponibilidad_linea('2026-01-01', '2026-06-30');

-- call sp  -- Línea huérfana eliminada
-- =====================================================================
-- Procedimiento 3: sp_registrar_salida_refaccion
-- =====================================================================
-- Objetivo: registrar la salida de una refaccion del almacen (cuando un
--           tecnico la instala en una maquina) dejando el registro
--           correspondiente en MOVIMIENTO de forma atomica. La salida NO
--           descontara el stock total: el stock de REFACCION es la suma
--           de la M:M ESTADO_REFACCION y la salida solo mueve 1 unidad de
--           DISPO a INMAQ (la unidad queda "instalada en maquina", sigue
--           contando en el total pero ya no esta disponible).
-- Parámetros:
--   refaccion    -> REFACCION.numeroRegistro
--   orden        -> folio de la orden de mantenimiento (puede ser NULL)
--   descripcion  -> texto libre para el movimiento
--   fecha        -> fecha del movimiento (si es NULL se usa CURDATE())
--   hora         -> hora del movimiento (si es NULL se usa CURTIME())
--   pieza        -> PIEZA.numeroSerie que se instala (puede ser NULL)
-- Lógica:
--   1a) Valida que la refaccion exista (independiente de su stock, para
--       que el INNER JOIN del paso 1b no confunda "no existe" con
--       "sin stock DISPO").
--   1b) Ubica la cantidad DISPO actual en ESTADO_REFACCION (INNER JOIN).
--   2) Valida que haya al menos 1 DISPO.
--   3) Valida la pieza si se indica.
--   4) Valida ANTES de tocar la M:M que la refaccion no este ya instalada
--      (no exista fila INMAQ): asi no se descuenta DISPO sin contraparte
--      y el error es descriptivo, no el 1062 de clave duplicada.
--   5) Mueve 1 unidad en la M:M: DISPO -1 e INMAQ +1.
--   6) Deja el registro de auditoria en MOVIMIENTO (tipo INSTA) con la
--      fecha/hora indicadas (o las del sistema) y la pieza instalada.
--   7) Devuelve la cantidad DISPO resultante y el numeroRegistro del
--      movimiento creado.
-- =====================================================================

-- DOCUMENTADO

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
    DECLARE numero_refaccion INT;
    DECLARE disponible      INT DEFAULT 0;
    DECLARE existe_pieza    INT;
    DECLARE existe_inmaq    INT DEFAULT 0;
    DECLARE existe_refaccion INT;
    DECLARE fechaP DATE;
    DECLARE horaP TIME;

    set fechaP = CURRENT_DATE();
    set horaP = CURRENT_TIME();

    -- 1a) validar que la refaccion exista (independiente de su stock:
    --     asi el INNER JOIN del paso 1b no confunde "no existe" con
    --     "sin stock DISPO").
    SELECT COUNT(*) INTO existe_refaccion
    FROM REFACCION
    WHERE numeroRegistro =  refaccion;

    IF existe_refaccion = 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La refaccion especificada no existe';
    END IF;

    -- 1b) cantidad DISPO actual de la refaccion (M:M). El INNER JOIN solo
    --     devuelve fila si la refaccion tiene estado DISPO; el caso "existe
    --     pero sin fila DISPO" cae en el paso 2 con mensaje correcto.
    --     (SELECT refaccion) fuerza el parametro: ESTADO_REFACCION tambien
    --     tiene una columna "refaccion" y MySQL preferiria la columna si se
    --     deja sin calificar.
    SELECT r.numeroRegistro, IFNULL(e.cantidad, 0)
    INTO numero_refaccion, disponible
    FROM REFACCION AS r
    INNER JOIN ESTADO_REFACCION AS e
           ON e.refaccion = r.numeroRegistro
          AND e.estado_refaccion = 'DISPO'
    WHERE r.numeroRegistro =  refaccion;

    -- 2) validar que haya al menos una unidad disponible (DISPO)
    IF disponible < 1 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cantidad disponible insuficiente para la salida de refaccion';
    END IF;

    -- 3) validar la pieza si se indica
    IF pieza IS NOT NULL THEN
        SELECT COUNT(*) INTO existe_pieza
        FROM PIEZA
        WHERE numeroSerie = pieza;

        IF existe_pieza = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La pieza especificada no existe';
        END IF;
    END IF;

    -- 4) validar ANTES de tocar la M:M que la refaccion no este ya
    --    instalada (no exista fila INMAQ). Asi el error es claro y, sobre
    --    todo, no se descuenta DISPO si el INSERT de INMAQ fallaria.
    --    OJO: hay que calificar con el alias (e.refaccion) porque si no
    --    MySQL resuelve `refaccion` al PARAMETRO del procedimiento, que
    --    eclipsa la columna, y el COUNT cuenta TODAS las filas INMAQ
    --    (refaccion = numero_refaccion siempre verdadero).
    SELECT COUNT(*) INTO existe_inmaq
    FROM ESTADO_REFACCION AS e
    WHERE e.estado_refaccion = 'INMAQ'
      AND e.refaccion = numero_refaccion;

    IF existe_inmaq > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La refaccion ya esta instalada en una maquina';
    END IF;

    -- 5) mover 1 unidad DISPO -> INMAQ en la tabla M:M ESTADO_REFACCION
    UPDATE ESTADO_REFACCION AS e
    SET e.cantidad = e.cantidad - 1
    WHERE e.estado_refaccion = 'DISPO'
      AND e.refaccion = numero_refaccion;

    INSERT INTO ESTADO_REFACCION (estado_refaccion, refaccion, cantidad)
    VALUES ('INMAQ', numero_refaccion, 1);

    -- 6) dejar el registro de auditoria en MOVIMIENTO (tipo INSTA) con la
    --    fecha/hora indicadas (o las del sistema) y la pieza instalada.
    INSERT INTO MOVIMIENTO (descripcion, fecha, hora, tipoMovimiento, orden_mantenimiento, refaccion, PIEZA)
    VALUES (descripcion, fechaP, horaP, 'INSTA', orden, numero_refaccion, pieza);

    -- 7) informar el resultado a quien llamo el procedimiento: el
    --    endpoint MovimientoCreateAPIView espera ESTE result set (si no
    --    hay SELECT final, cur.description viene en None y falla).
    SELECT (disponible - 1) AS stock_resultante,
           LAST_INSERT_ID() AS numero_movimiento;
END $$

DELIMITER ;

-- Llamada (igual que el ejemplo):
-- call srendimiento_trabajador('NOM-001', @nombre, @asignadas, @cerradas);
-- select @nombre as Nombre, @asignadas as Ordenes_Asignadas, @cerradas as Ordenes_Cerradas;
-- Llamada (igual que el ejemplo):
-- call srendimiento_trabajador('NOM-001', @nombre, @asignadas, @cerradas);
-- select @nombre as Nombre, @asignadas as Ordenes_Asignadas, @cerradas as Ordenes_Cerradas;

-- =====================================================================
-- Procedimiento 6a: sp_resumen_maquina_maquinaria (antes sp_resumen_maquina,
--                    version de Misael)
-- =====================================================================
-- Objetivo: devolver la ficha resumen de una maquina (nombre, estado,
--           total de fallas, total de ordenes de mantenimiento, horas de
--           operacion acumuladas e indicadores vigentes: mtbf, mttr,
--           % disponibilidad, tiempo de inactividad y numero de
--           reparaciones). Lo consumen DOS endpoints:
--             - GET /maquinaria/v1/maquina/<codigo>/resumen/
--               (ResumenMaquinaAPIView, api/apps/maquinaria/views.py)
--             - GET /api/monitoreo/maquinas/<codigo>/indicadores/
--               (IndicadoresMaquinaAPIView, api/apps/monitoreo/views.py)
-- Parámetros:
--   maquina              -> MAQUINA.codigo (IN)
--   nombre               -> OUT: nombre de la maquina
--   estado               -> OUT: MAQUINA.estado_maquina (codigo, ej. OPERA)
--   total_fallas         -> OUT: total de reportes de falla de la maquina
--   total_ordenes        -> OUT: total de ordenes de mantenimiento
--   horas_operacion      -> OUT: suma de horas de operacion (REGISTRO_OPS)
--   mtbf                 -> OUT: MTBF del ultimo periodo
--   mttr                 -> OUT: MTTR del ultimo periodo
--   disponibilidad       -> OUT: % de disponibilidad del ultimo periodo
--   tiempo_inactividad   -> OUT: SUM(REPORTE_FALLA.tiempoParo) de fallas
--                                  con orden cerrada
--   numero_reparaciones  -> OUT: COUNT de ordenes cerradas con reporte
--                                  de falla
-- Lógica:
--   1) Wrapper delgado sobre la vista de apoyo v_kpi_indicadores_actuales
--      (backend/vistas_kpi.sql), que entrega la ficha completa calculada
--      en vivo (misma logica de los triggers de triggers2.sql) mas el
--      total de ordenes. El SP solo mapea columnas a parametros OUT con
--      SELECT INTO.
--   2) La vista es MAQUINA-céntrica (LEFT JOINs): si la maquina no tiene
--      indicadores todavia, igual devuelve fila y los OUT de KPI quedan
--      en NULL (los endpoints los convierten en 0 / "--").
--   3) Las columnas se califican con el alias v. A PROPOSITO: en MySQL,
--      dentro de un SP un nombre sin calificar que coincida con un
--      parametro/variable resuelve a la VARIABLE, no a la columna
--      (refman: local-variable-scope). Sin el alias, MTBF/MTTR/
--      Disponibilidad chocarian con los OUT mtbf/mttr/disponibilidad y
--      el SELECT INTO se auto-asignaria NULL (vacio) siempre.
--   Patron: SP que consume una vista de apoyo (igual que el SP1 con
--   v_periodo_abierto_maquina y el SP3 con la M:M ESTADO_REFACCION).
-- =====================================================================

-- DOCUMENTADO

DROP PROCEDURE IF EXISTS sp_resumen_maquina_maquinaria;

DELIMITER $$

CREATE PROCEDURE sp_resumen_maquina(
    IN  maquina             VARCHAR(10),
    OUT nombre              VARCHAR(100),
    OUT estado              VARCHAR(5),
    OUT total_fallas        INT,
    OUT total_ordenes       INT,
    OUT horas_operacion     INT,
    OUT mtbf                FLOAT,
    OUT mttr                FLOAT,
    OUT disponibilidad      INT,
    OUT tiempo_inactividad  INT,
    OUT numero_reparaciones INT
)
BEGIN
    SELECT
        v.Maquina,
        v.EstadoCodigo,
        v.TotalFallas,
        v.TotalOrdenes,
        v.TotalHorasOperacion,
        v.MTBF,
        v.MTTR,
        v.Disponibilidad,
        v.TiempoTotalParo,
        v.NumReparaciones
    INTO
        nombre,
        estado,
        total_fallas,
        total_ordenes,
        horas_operacion,
        mtbf,
        mttr,
        disponibilidad,
        tiempo_inactividad,
        numero_reparaciones
    FROM v_kpi_indicadores_actuales AS v
    WHERE v.Codigo = maquina;
END $$

DELIMITER ;

-- Llamada:
-- call sp_historial_maquina('MAQ001');

-- =====================================================================
-- Procedimiento 8: sp_perfil_trabajador
-- =====================================================================
-- Objetivo: devolver los 5 contadores que muestra el encabezado del
--           perfil del trabajador (client/templates/mantenimiento/
--           trabajador_detalle.html): ordenes asignadas, cerradas,
--           pendientes, fallas reportadas y maquinas atendidas. Todos
--           via parametros OUT (mismo patron que sp_rendimiento_
--           trabajador). Las LISTAS de ordenes/reportes siguen viniendo
--           de los endpoints de la API.
-- Parámetros:
--   nomina              -> TRABAJADOR.numeroNomina (IN)
--   ordenes_asignadas   -> OUT: total de ordenes del trabajador
--   ordenes_cerradas    -> OUT: ordenes con estado 'CERRA'
--   ordenes_pendientes  -> OUT: ordenes sin estado o con estado distinto
--                           de 'CERRA'/'CANCE'
--   fallas_reportadas   -> OUT: total de reportes de falla del trabajador
--   maquinas_atendidas  -> OUT: maquinas tocadas por el trabajador = suma
--                           de las de ORDEN_MANTENIMIENTO + las de
--                           REPORTE_FALLA (si una maquina esta en ambas
--                           tablas se cuenta dos veces)
-- Lógica:
--   1) Cada contador es un SELECT COUNT(*) ... INTO <OUT>. COUNT sobre
--      un conjunto vacio devuelve 0, nunca NULL, asi que una nomina sin
--      actividad (o inexistente) produce 0s en lugar de errores.
--   2) maquinas_atendidas: dos SELECT COUNT(DISTINCT maquina) por separado
--      (uno por tabla) que se suman en variables locales; la suma NO
--      deduplica entre tablas.
--   3) (SELECT nomina): fuerza el parametro (mismo patron que SP1/SP3/SP6)
--      por si alguna tabla tiene columna con el mismo nombre.
-- =====================================================================

-- DOCUMENTADO

DROP PROCEDURE IF EXISTS sp_perfil_trabajador;

DELIMITER $$

CREATE PROCEDURE sp_perfil_trabajador(
    IN  nomina             VARCHAR(15),
    OUT ordenes_asignadas  INT,
    OUT ordenes_cerradas   INT,
    OUT ordenes_pendientes INT,
    OUT fallas_reportadas  INT,
    OUT maquinas_atendidas INT
)
BEGIN
    DECLARE maquinas_ordenes  INT DEFAULT 0;
    DECLARE maquinas_reportes INT DEFAULT 0;

    -- 1) ordenes asignadas (todas las ordenes del trabajador)
    SELECT COUNT(*)
    INTO ordenes_asignadas
    FROM ORDEN_MANTENIMIENTO as o
    WHERE o.trabajador = nomina;

    -- 2) ordenes cerradas (estado 'CERRA')
    SELECT COUNT(*)
    INTO ordenes_cerradas
    FROM ORDEN_MANTENIMIENTO as o
    WHERE o.trabajador =  nomina
      AND o.estado_orden = 'CERRA';

    -- 3) ordenes pendientes (sin estado o con estado distinto de
    --    'CERRA'/'CANCE'; incluye estado NULL)
    SELECT COUNT(*)
    INTO ordenes_pendientes
    FROM ORDEN_MANTENIMIENTO as o
    WHERE o.trabajador = nomina
      AND (o.estado_orden NOT IN ('CERRA', 'CANCE') OR o.estado_orden IS NULL);

    -- 4) fallas reportadas
    SELECT COUNT(*)
    INTO fallas_reportadas
    FROM REPORTE_FALLA as rf
    WHERE rf.trabajador = (SELECT nomina);

    -- 5) maquinas atendidas: dos consultas separadas (una por tabla) que
    --    se suman en variables locales. OJO: si una maquina aparece en
    --    ORDEN_MANTENIMIENTO y en REPORTE_FALLA se cuenta dos veces (la
    --    suma no deduplica entre tablas).
    SELECT COUNT(DISTINCT o.maquina)
    INTO maquinas_ordenes
    FROM ORDEN_MANTENIMIENTO as o
    WHERE o.trabajador = nomina AND o.maquina IS NOT NULL;

    SELECT COUNT(DISTINCT rf.maquina)
    INTO maquinas_reportes
    FROM REPORTE_FALLA as rf
    WHERE rf.trabajador = nomina;

    SET maquinas_atendidas = maquinas_ordenes + maquinas_reportes;
END $$

DELIMITER ;

-- Llamada:
-- call sp_perfil_trabajador('NOM-001', @asignadas, @cerradas, @pendientes, @fallas, @maquinas);
-- select @asignadas, @cerradas, @pendientes, @fallas, @maquinas;


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
--   2) Concatena nombre + apellidoPat + apellidoMat (con IFNULL por si
--      el segundo apellido no existe).
--   3) Cuenta el total de ordenes asignadas (COUNT) y las cerradas (una
--      subconsulta con COUNT(*)... estado_orden = 'CERRA').
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
        CONCAT(t.nombre, ' ', t.apellidoPat, ' ', ifnull(t.apellidoMat, '')),
        COUNT(o.folio),
        (SELECT COUNT(*)
         FROM ORDEN_MANTENIMIENTO o2
         WHERE o2.trabajador = t.numeroNomina
           AND o2.estado_orden = 'CERRA')
    INTO nombre, ordenes_asignadas, ordenes_cerradas
    FROM TRABAJADOR as t
    INNER JOIN ORDEN_MANTENIMIENTO o ON o.trabajador = t.numeroNomina
    WHERE t.numeroNomina = nomina
    GROUP BY t.numeroNomina;
END $$

DELIMITER ;



-- Llamada:
-- call sp_resumen_maquina('MAQ001', @nombre, @estado, @fallas, @ordenes, @horas,
--                         @mtbf, @mttr, @dispo, @inactividad, @reparaciones);
-- select @nombre, @estado, @fallas, @ordenes, @horas,
--        @mtbf, @mttr, @dispo, @inactividad, @reparaciones;

/* =====================================================================
   FRAGMENTOS PREVIOS DE sp_resumen_maquina (solo referencia, no se usan)
   ---------------------------------------------------------------------
   Version A - ficha del drawer de Monitoreo (1 IN + 9 OUT), leia la vista:
   ---------------------------------------------------------------------
   CREATE PROCEDURE sp_resumen_maquina(
       IN  maquina             VARCHAR(10),
       OUT nombre              VARCHAR(100),
       OUT estado              VARCHAR(50),
       OUT mtbf                FLOAT,
       OUT mttr                FLOAT,
       OUT disponibilidad      INT,
       OUT total_horas         INT,
       OUT numero_fallas       INT,
       OUT tiempo_inactividad  INT,
       OUT numero_reparaciones INT
   )
   BEGIN
       SELECT Maquina, Estado, MTTR, MTBF, Disponibilidad,
              TotalHorasOperacion, TotalFallas, TiempoTotalParo, NumReparaciones
       INTO nombre, estado, mttr, mtbf, disponibilidad,
            total_horas, numero_fallas, tiempo_inactividad, numero_reparaciones
       FROM v_kpi_indicadores_actuales
       WHERE Codigo = maquina;
   END $$
   ---------------------------------------------------------------------
   Version B - resumen de Maquinaria (1 IN + 8 OUT), consultas inline:
   ---------------------------------------------------------------------
   CREATE PROCEDURE sp_resumen_maquina(
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
       SELECT m.nombre, m.estado_maquina,
              COUNT(DISTINCT rf.numeroRegistro),
              COUNT(DISTINCT om.folio),
              ( SELECT IFNULL(SUM(ro.horasOperacion), 0)
                FROM REGISTRO_OPS ro WHERE ro.maquina = m.codigo )
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
   ===================================================================== */

-- =====================================================================
-- Procedimiento 7: sp_historial_maquina
-- =====================================================================
-- Objetivo: devolver, en un solo result set, todas las ordenes de
--           mantenimiento y todos los reportes de falla de una maquina,
--           con el trabajador que atendio cada uno. Va como result set
--           (no OUT) porque es una lista de N filas, no un escalar.
-- Parámetros:
--   maquina -> MAQUINA.codigo
-- Lógica:
--   1) UNION ALL entre ORDEN_MANTENIMIENTO y REPORTE_FALLA, marcando el
--      tipo de cada fila ('ORDEN' / 'FALLA').
--   2) Nombre del trabajador via subconsulta escalar (trabajador puede ser
--      NULL en ordenes: la subconsulta devuelve NULL, igual que el LEFT
--      JOIN original).
--   3) Ordena todo por fecha descendente (mas reciente primero).
-- =====================================================================
DROP PROCEDURE IF EXISTS sp_historial_maquina;

DELIMITER $$

CREATE PROCEDURE sp_historial_maquina(
    IN maquina VARCHAR(10)
)
BEGIN
    SELECT
        'ORDEN' AS tipo,
        om.folio AS identificador,
        om.fechaCreacion AS fecha,
        om.descripcion AS detalle,
        om.estado_orden AS estado,
        om.trabajador AS trabajador_nomina,
        (SELECT CONCAT(t.nombre, ' ', t.apellidoPat, ' ', IFNULL(t.apellidoMat, ''))
         FROM TRABAJADOR as t WHERE t.numeroNomina = om.trabajador) AS trabajador_nombre
    FROM ORDEN_MANTENIMIENTO as om
    WHERE om.maquina = maquina

    UNION ALL

    SELECT
        'FALLA' AS tipo,
        CAST(rf.numeroRegistro AS CHAR) AS identificador,
        rf.fechaCreacion AS fecha,
        rf.asunto AS detalle,
        rf.estado_reporte AS estado,
        rf.trabajador AS trabajador_nomina,
        (SELECT CONCAT(t.nombre, ' ', t.apellidoPat, ' ', IFNULL(t.apellidoMat, ''))
         FROM TRABAJADOR as t WHERE t.numeroNomina = rf.trabajador) AS trabajador_nombre
    FROM REPORTE_FALLA as rf
    WHERE rf.maquina = maquina

    ORDER BY fecha DESC;
END $$

DELIMITER ;

