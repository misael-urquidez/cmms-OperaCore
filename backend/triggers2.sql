-- ---------- triggers del proyecto -------------

USE operacore;

/*
Trigger 1
Este trigger recalcula el MTBF de la máquina a la que pertenece el nuevo registro.
Si la máquina aún no tiene un registro en INDICADOR, lo crea automáticamente.

-- Trigger: tg_actualizar_mtbf_registroops
-- Evento: se dispara después de cada INSERT en REGISTRO_OPS
-- Objetivo: recalcular el MTBF (tiempo medio entre fallas) de la
--           máquina afectada y guardarlo en INDICADOR como histórico
--           por periodo (no como valor único por máquina).
-- Lógica de periodos: INDICADOR maneja historial; el periodo "vigente"
--           de una máquina es el que tiene fechaFin = NULL. Si no
--           existe un periodo abierto, se crea uno nuevo; si ya existe,
--           se actualiza. Cerrar un periodo (poner fechaFin) es
--           responsabilidad de otro proceso externo al trigger.
*/

DROP TRIGGER IF EXISTS tg_actualizar_mtbf_registroops;

DELIMITER $$

CREATE TRIGGER tg_actualizar_mtbf_registroops
AFTER INSERT ON REGISTRO_OPS
FOR EACH ROW
BEGIN
    DECLARE totalHoras INT;
    DECLARE totalFallas INT;
    DECLARE nuevoMTBF FLOAT;
    DECLARE existePeriodoAbierto INT;

    -- Horas totales de operación de la máquina (acumulado histórico)
    SELECT IFNULL(SUM(horasOperacion),0)
    INTO totalHoras
    FROM REGISTRO_OPS
    WHERE maquina = NEW.maquina;

    -- Número de fallas de la máquina (acumulado histórico)
    SELECT COUNT(*)
    INTO totalFallas
    FROM REPORTE_FALLA
    WHERE maquina = NEW.maquina;

    IF totalFallas > 0 THEN
        SET nuevoMTBF = totalHoras / totalFallas;
    ELSE
        SET nuevoMTBF = NULL;
    END IF;

    -- Verificar si ya existe un periodo "abierto" (vigente) para la máquina
    SELECT COUNT(*)
    INTO existePeriodoAbierto
    FROM INDICADOR
    WHERE maquina = NEW.maquina AND fechaFin IS NULL;

    IF existePeriodoAbierto = 0 THEN
        -- No hay periodo abierto: crear uno nuevo
        INSERT INTO INDICADOR(maquina, fechaInicio, mtbf)
        VALUES (NEW.maquina, NEW.fechaInicio, nuevoMTBF);
    ELSE
        -- Ya hay un periodo abierto: actualizar solo ese
        UPDATE INDICADOR
        SET mtbf = nuevoMTBF
        WHERE maquina = NEW.maquina AND fechaFin IS NULL;
    END IF;

END$$

DELIMITER ;

/*
-- Trigger: tg_actualizar_mttr_orden
-- Evento: se dispara DESPUÉS de un UPDATE en ORDEN_MANTENIMIENTO
-- Objetivo: cuando una orden pasa de "abierta" a "cerrada" (se le
--           asigna fechaCierre), recalcula el MTTR de la máquina
--           afectada y lo guarda en el periodo vigente de INDICADOR
--           (mismo criterio de historial que el trigger de MTBF:
--           el periodo vigente es el que tiene fechaFin = NULL).
-- Condición clave: solo debe recalcular si la orden se ACABA de
--           cerrar en este UPDATE (antes NULL, ahora con fecha),
--           para no recalcular en cada edición menor de la orden.
*/

DROP TRIGGER IF EXISTS tg_actualizar_mttr_orden;

DELIMITER $$

CREATE TRIGGER tg_actualizar_mttr_orden
AFTER UPDATE ON ORDEN_MANTENIMIENTO
FOR EACH ROW
BEGIN
    DECLARE sumaTiempoParo INT;
    DECLARE numReparaciones INT;
    DECLARE nuevoMTTR FLOAT;
    DECLARE existePeriodoAbierto INT;

    -- filtro: solo actúa si la orden se acaba de cerrar en este UPDATE
    -- (antes no tenía fechaCierre, ahora sí la tiene)
    IF OLD.fechaCierre IS NULL AND NEW.fechaCierre IS NOT NULL THEN

        -- 1. suma del tiempo de paro de las fallas de órdenes cerradas de esa máquina
        SELECT IFNULL(SUM(rf.tiempoParo), 0)
        INTO sumaTiempoParo
        FROM REPORTE_FALLA AS rf
        INNER JOIN ORDEN_MANTENIMIENTO AS om ON rf.numeroRegistro = om.reporte_falla
        WHERE om.maquina = NEW.maquina
          AND om.fechaCierre IS NOT NULL;

        -- 2. número de reparaciones = órdenes cerradas de esa máquina
        SELECT COUNT(*)
        INTO numReparaciones
        FROM ORDEN_MANTENIMIENTO
        WHERE maquina = NEW.maquina
          AND fechaCierre IS NOT NULL;

        -- 3. MTTR = tiempo total de paro / número de reparaciones
        IF numReparaciones > 0 THEN
            SET nuevoMTTR = sumaTiempoParo / numReparaciones;
        ELSE
            SET nuevoMTTR = NULL;
        END IF;

        -- 4. ¿existe un periodo vigente (fechaFin NULL) en INDICADOR?
        SELECT COUNT(*)
        INTO existePeriodoAbierto
        FROM INDICADOR
        WHERE maquina = NEW.maquina AND fechaFin IS NULL;

        -- 5a. no existe -> crear periodo nuevo con el MTTR calculado
        IF existePeriodoAbierto = 0 THEN
            INSERT INTO INDICADOR (maquina, fechaInicio, mttr)
            VALUES (NEW.maquina, NEW.fechaCierre, nuevoMTTR);
        ELSE
            -- 5b. ya existe -> solo actualizar su MTTR
            UPDATE INDICADOR
            SET mttr = nuevoMTTR
            WHERE maquina = NEW.maquina AND fechaFin IS NULL;
        END IF;

    END IF;
END$$

DELIMITER ;

/*
Tercer trigger para calcular la disponibilidad
*/

DROP TRIGGER IF EXISTS tg_actualizar_disponibilidad_indicador;

DELIMITER $$

CREATE TRIGGER tg_actualizar_disponibilidad_indicador
BEFORE UPDATE ON INDICADOR
FOR EACH ROW
BEGIN
    DECLARE nuevaDisponibilidad INT;

    IF (NOT(NEW.mtbf <=> OLD.mtbf)) OR (NOT(NEW.mttr <=> OLD.mttr)) THEN
        IF NEW.mtbf IS NOT NULL AND NEW.mttr IS NOT NULL AND (NEW.mtbf + NEW.mttr) > 0 THEN
            SET nuevaDisponibilidad = ROUND((NEW.mtbf / (NEW.mtbf + NEW.mttr)) * 100);
        ELSE
            SET nuevaDisponibilidad = NULL;
        END IF;

        SET NEW.porcentajeDispo = nuevaDisponibilidad;

    END IF;
END$$

DELIMITER ;

DROP TRIGGER IF EXISTS tg_disponibilidad_indicador_insert;

DELIMITER $$

CREATE TRIGGER tg_disponibilidad_indicador_insert
BEFORE INSERT ON INDICADOR
FOR EACH ROW
BEGIN
    DECLARE nuevaDisponibilidad INT;

    IF NEW.mtbf IS NOT NULL AND NEW.mttr IS NOT NULL AND (NEW.mtbf + NEW.mttr) > 0 THEN
        SET nuevaDisponibilidad = ROUND((NEW.mtbf / (NEW.mtbf + NEW.mttr)) * 100);
    ELSE
        SET nuevaDisponibilidad = NULL;
    END IF;

    SET NEW.porcentajeDispo = nuevaDisponibilidad;
END$$

DELIMITER ;

/*
Trigger 6 y 7
Validan que el tipo_maquina asignado a una MAQUINA sea compatible con el
área a la que pertenece su línea, usando la tabla puente TIPO_MAQUINA_AREA.

-- Evento: BEFORE INSERT / BEFORE UPDATE en MAQUINA
-- Objetivo: si el tipo_maquina tiene alguna fila en TIPO_MAQUINA_AREA,
--           se considera restringido y solo puede insertarse/actualizarse
--           si existe una fila (tipo_maquina, area_de_la_linea). Si el
--           tipo_maquina no tiene ninguna fila en TIPO_MAQUINA_AREA, se
--           considera UNIVERSAL y no se valida nada.
-- Nota: esta es la garantía real a nivel de base de datos; las apps
--       Django (fallas/monitoreo y maquinaria) duplican esta misma
--       regla en sus serializers solo para dar un mensaje 400 legible
--       en vez de dejar que el INSERT/UPDATE truene con un 500.
*/

DROP TRIGGER IF EXISTS tg_validar_tipo_maquina_area_insert;
DELIMITER $$
CREATE TRIGGER tg_validar_tipo_maquina_area_insert
BEFORE INSERT ON MAQUINA
FOR EACH ROW
BEGIN
    DECLARE areaLinea VARCHAR(10);
    DECLARE tieneRestriccion INT;
    DECLARE esCompatible INT;

    IF NEW.linea IS NOT NULL AND NEW.tipo_maquina IS NOT NULL THEN
        SELECT area INTO areaLinea FROM LINEA WHERE codigo = NEW.linea;

        SELECT COUNT(*) INTO tieneRestriccion
        FROM TIPO_MAQUINA_AREA WHERE tipo_maquina = NEW.tipo_maquina;

        IF tieneRestriccion > 0 THEN
            SELECT COUNT(*) INTO esCompatible
            FROM TIPO_MAQUINA_AREA
            WHERE tipo_maquina = NEW.tipo_maquina AND area = areaLinea;

            IF esCompatible = 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Este tipo de máquina no está autorizado para el área de esa línea.';
            END IF;
        END IF;
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_validar_tipo_maquina_area_update;
DELIMITER $$
CREATE TRIGGER tg_validar_tipo_maquina_area_update
BEFORE UPDATE ON MAQUINA
FOR EACH ROW
BEGIN
    DECLARE areaLinea VARCHAR(10);
    DECLARE tieneRestriccion INT;
    DECLARE esCompatible INT;

    IF NEW.linea IS NOT NULL AND NEW.tipo_maquina IS NOT NULL THEN
        SELECT area INTO areaLinea FROM LINEA WHERE codigo = NEW.linea;

        SELECT COUNT(*) INTO tieneRestriccion
        FROM TIPO_MAQUINA_AREA WHERE tipo_maquina = NEW.tipo_maquina;

        IF tieneRestriccion > 0 THEN
            SELECT COUNT(*) INTO esCompatible
            FROM TIPO_MAQUINA_AREA
            WHERE tipo_maquina = NEW.tipo_maquina AND area = areaLinea;

            IF esCompatible = 0 THEN
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Este tipo de máquina no está autorizado para el área de esa línea.';
            END IF;
        END IF;
    END IF;
END$$
DELIMITER ;