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

-- =====================================================================
-- 📍 IMPLEMENTACIÓN EN EL PROYECTO (tg_actualizar_mtbf_registroops)
-- Se dispara cuando el backend hace INSERT en REGISTRO_OPS. Eso ocurre en:
--   Archivo: api/apps/monitoreo/views.py
--   Clase:   RegistroOpsAPIView.post (línea 308)
--   Llamada: services.registrar_horas_operacion(...) -> línea 314
--   Archivo: api/apps/monitoreo/services.py
--   Función: registrar_horas_operacion -> RegistroOps.objects.create(...) (línea 120)
--   Endpoint (urls.py): POST /monitoreo/maquinas/<codigo>/registro-ops/
--            (api/apps/monitoreo/urls.py, name="registro-ops")
-- Frontend (formulario, captura ya revisada):
--   Módulo Indicadores -> "Horas de Operación" (Fecha inicio, Fecha fin,
--   Horas operadas, botón "Registrar horas")
-- =====================================================================

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

-- =====================================================================
-- 📍 IMPLEMENTACIÓN EN EL PROYECTO (tg_actualizar_mttr_orden)
-- Se dispara cuando el backend hace UPDATE en ORDEN_MANTENIMIENTO
-- poniéndole fechaCierre por primera vez. Eso ocurre en:
--   Archivo: api/apps/mantenimiento/views.py
--   Clase:   OrdenMantenimientoCerrarAPIView.patch (línea 522)
--   Líneas clave: 546-547
--     orden.fechacierre, orden.horacierre, orden.estado_orden_id = ...
--     orden.save(update_fields=[..., "fechacierre", ...])
--   Endpoint (urls.py): PATCH /mantenimiento/v2/ordenes/<folio>/cerrar/
--            (api/apps/mantenimiento/urls.py, name="ordenes-cerrar")
-- Frontend:
--   Módulo Mantenimiento -> detalle de una orden -> acción "Cerrar orden"
-- Nota (visto en la conversación): el propio comentario del código en
-- mantenimiento/views.py (línea 534) explica que el reporte de falla se
-- cierra ANTES de guardar fechaCierre en la orden, para que este trigger
-- lea el tiempoParo ya actualizado -- ambos saves van en la misma
-- transacción (@transaction.atomic).
-- =====================================================================

DELIMITER $$

CREATE TRIGGER tg_actualizar_mttr_orden
AFTER UPDATE ON ORDEN_MANTENIMIENTO
FOR EACH ROW
BEGIN
    DECLARE sumaTiempoParo DECIMAL(8,2);
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

        -- 2. número de reparaciones = ordenes CORRECTIVAS cerradas de esa
        -- máquina (mismo criterio que el numerador arriba: solo cuentan
        -- las que de verdad vienen de un reporte_falla, si no el MTTR se
        -- diluye con cierres de preventivo/predictivo/emergencia que
        -- nunca aportaron tiempoParo)
        SELECT COUNT(*)
        INTO numReparaciones
        FROM ORDEN_MANTENIMIENTO
        WHERE maquina = NEW.maquina
          AND fechaCierre IS NOT NULL
          AND reporte_falla IS NOT NULL;

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

-- =====================================================================
-- 📍 IMPLEMENTACIÓN EN EL PROYECTO
-- (tg_actualizar_disponibilidad_indicador y tg_disponibilidad_indicador_insert)
-- No los dispara un formulario directo: se disparan EN CADENA cada vez
-- que algo hace UPDATE/INSERT sobre INDICADOR, es decir, cada vez que:
--   - tg_actualizar_mtbf_registroops actualiza/inserta INDICADOR
--     (ver arriba: formulario "Horas de Operación")
--   - tg_actualizar_mttr_orden actualiza/inserta INDICADOR
--     (ver arriba: "Cerrar orden")
--   - sp_cerrar_periodo_indicador hace el INSERT del periodo nuevo
--     (backend/sp.sql, Procedimiento 1) -> disparado desde
--     api/apps/indicadores/views.py, clase CerrarPeriodoIndicadorAPIView
--     (línea 587), botón "Cerrar periodo" del módulo Indicadores
-- Por eso NO tienen una sola pantalla de origen: son la "última milla"
-- que recalcula porcentajeDispo cada vez que cambian mtbf/mttr, sin
-- importar qué proceso los cambió.
-- =====================================================================

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

-- =====================================================================
-- 📍 IMPLEMENTACIÓN EN EL PROYECTO
-- (tg_validar_tipo_maquina_area_insert y ..._update)
-- INSERT se dispara al crear una máquina:
--   Archivo: api/apps/maquinaria/serializers.py
--   Clase:   CreateMaquinaSerializer (línea 315), método create (línea 340)
--   Endpoint (urls.py): POST /maquinaria/v1/maquina/create/
--            (views.CrearMaquinaAPIView, name="create_maquina")
-- UPDATE se dispara al editar una máquina:
--   Archivo: api/apps/maquinaria/serializers.py
--   Clase:   UpdateMaquinaSerializer (línea 358)
--   Endpoint (urls.py): PATCH/PUT /maquinaria/v1/maquina/update/<codigo>/
--            (views.UpdateMaquinaAPIView, name="update_maquina")
-- Nota: ambos serializers usan ValidarTipoMaquinaAreaMixin, que duplica
-- esta misma regla en Django (mismo criterio que documenta el propio
-- comentario del trigger) solo para dar un 400 legible antes de que
-- llegue a tronar el INSERT/UPDATE con el SIGNAL de MySQL.
-- Frontend:
--   Módulo Maquinaria -> "Registrar máquina" / editar máquina (selects
--   de Línea y Tipo de máquina)
-- =====================================================================

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

-- =====================================================================
-- INVENTARIO: ESTADO_REFACCION como desglose del stock (M:M).
-- REFACCION.stock es el TOTAL en almacen = SUMA de las cantidades por
-- estado en ESTADO_REFACCION (ej. stock 10 = DISPO 5 + ENREP 3 + INMAQ 2).
-- Estos triggers mantienen esa invariante automaticamente:
--   * Al insertar una REFACCION se pre-crea su fila DISPO = stock, para
--     que el CRUD de refacciones (que solo escribe REFACCION.stock)
--     quede poblado en la M:M y sp_registrar_salida_refaccion funcione.
--   * Cualquier INSERT/UPDATE/DELETE sobre ESTADO_REFACCION (el SP3 o el
--     CRUD "Estados de refacción") recalcula REFACCION.stock.
-- =====================================================================

DROP TRIGGER IF EXISTS tg_seed_estado_dispo;

-- =====================================================================
-- 📍 IMPLEMENTACIÓN EN EL PROYECTO
-- (tg_seed_estado_dispo, tg_sync_refaccion_stock_insert/update/delete)
--
-- tg_seed_estado_dispo se dispara al crear una refacción:
--   Archivo: api/apps/inventario/views.py
--   Clase:   RefaccionCreateAPIView (línea 334)
--   Endpoint (urls.py): POST /inventario/v2/refacciones/create/
--            (name="refacciones-create")
--   Frontend: módulo Inventario -> "Registrar refacción"
--
-- tg_sync_refaccion_stock_insert/update/delete se disparan cada vez que
-- se toca ESTADO_REFACCION (la tabla M:M), lo cual pasa en DOS lugares:
--   1) sp_registrar_salida_refaccion (backend/sp.sql, Procedimiento 3)
--      -> UPDATE + INSERT sobre ESTADO_REFACCION (líneas 337-341 de ese SP)
--      Disparado desde:
--        api/apps/inventario/views.py, RegistrarSalidaRefaccionAPIView
--          (línea 477), POST /inventario/v2/movimientos/salida-refaccion/
--        api/apps/mantenimiento/views.py, _call_sp_salida_refaccion
--          (línea 192), al instalar una refacción desde una orden
--   2) CRUD manual "Estados de refacción" (create/update/delete directo
--      sobre la tabla M:M):
--      Archivo: api/apps/inventario/views.py
--      Clases:  EstadoRefaccionCreateAPIView (línea 424),
--               EstadoRefaccionDetailAPIView (línea 428, PUT/PATCH/DELETE)
--      Endpoint (urls.py): /inventario/v1/existencia-refaccion/...
--               (name="existencia-refaccion-create"/"-detail")
-- =====================================================================

DELIMITER $$
CREATE TRIGGER tg_seed_estado_dispo
AFTER INSERT ON REFACCION
FOR EACH ROW
BEGIN
    INSERT INTO ESTADO_REFACCION (estado_refaccion, refaccion, cantidad)
    VALUES ('DISPO', NEW.numeroRegistro, IFNULL(NEW.stock, 0))
    ON DUPLICATE KEY UPDATE cantidad = VALUES(cantidad);
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_sync_refaccion_stock_insert;
DELIMITER $$
CREATE TRIGGER tg_sync_refaccion_stock_insert
AFTER INSERT ON ESTADO_REFACCION
FOR EACH ROW
BEGIN
    UPDATE REFACCION r
    SET r.stock = (SELECT IFNULL(SUM(e.cantidad), 0)
                   FROM ESTADO_REFACCION e
                   WHERE e.refaccion = NEW.refaccion)
    WHERE r.numeroRegistro = NEW.refaccion;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_sync_refaccion_stock_update;
DELIMITER $$
CREATE TRIGGER tg_sync_refaccion_stock_update
AFTER UPDATE ON ESTADO_REFACCION
FOR EACH ROW
BEGIN
    UPDATE REFACCION r
    SET r.stock = (SELECT IFNULL(SUM(e.cantidad), 0)
                   FROM ESTADO_REFACCION e
                   WHERE e.refaccion = NEW.refaccion)
    WHERE r.numeroRegistro = NEW.refaccion;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_sync_refaccion_stock_delete;
DELIMITER $$
CREATE TRIGGER tg_sync_refaccion_stock_delete
AFTER DELETE ON ESTADO_REFACCION
FOR EACH ROW
BEGIN
    UPDATE REFACCION r
    SET r.stock = (SELECT IFNULL(SUM(e.cantidad), 0)
                   FROM ESTADO_REFACCION e
                   WHERE e.refaccion = OLD.refaccion)
    WHERE r.numeroRegistro = OLD.refaccion;
END$$
DELIMITER ;

-- =====================================================================
-- REPORTE_FALLA: FECHA DE RESOLUCIÓN AUTOMÁTICA AL CERRAR.
-- La fecha de resolución ya no se captura en el formulario: se carga
-- sola cuando el estado del reporte pasa a 'CERRA' (Cerrado).
--   * INSERT: si un reporte se da de alta directamente como cerrado, se
--     le pone la fecha de hoy.
--   * UPDATE: solo actúa cuando el estado ACABA de pasar a CERRA (antes
--     no estaba en CERRA, ahora sí); si el reporte ya estaba cerrado y
--     solo se edita otra cosa, la fecha se conserva intacta.
-- Son BEFORE porque modifican NEW.fechaResolucion antes de escribirse.
-- =====================================================================

DROP TRIGGER IF EXISTS tg_fecharesolucion_cerrado_insert;

-- =====================================================================
-- 📍 IMPLEMENTACIÓN EN EL PROYECTO
-- (tg_fecharesolucion_cerrado_insert y tg_fecharesolucion_cerrado_update)
-- INSERT se dispara si un reporte se crea directo como 'CERRA':
--   Archivo: api/apps/fallas/views.py
--   Clase:   ReporteFallaCreateAPIView (línea 127)
--   Endpoint (urls.py): POST /fallas/v2/reportes/create/
--            (name="reportes-create")
-- UPDATE se dispara cuando un reporte pasa a 'CERRA' (desde otro estado):
--   Archivo: api/apps/fallas/views.py
--   Clase:   ReporteFallaUpdateAPIView (línea 147)
--   Endpoint (urls.py): PATCH/PUT /fallas/v2/reportes/update/<pk>/
--            (name="reportes-update")
--   También se dispara indirectamente al cerrar una orden de
--   mantenimiento con reporte de falla asociado: ver arriba
--   OrdenMantenimientoCerrarAPIView (mantenimiento/views.py línea 542,
--   reporte.estado_reporte_id = "RESUE" -- OJO: ese caso usa el estado
--   'RESUE', no 'CERRA', así que ESE guardado en particular NO dispara
--   este trigger; el reporte llega a 'CERRA' en un paso posterior/manual
--   vía fallas/views.py.
-- Frontend:
--   Módulo Fallas -> crear/editar reporte de falla -> cambiar estado a
--   "Cerrado"
-- =====================================================================

DELIMITER $$
CREATE TRIGGER tg_fecharesolucion_cerrado_insert
BEFORE INSERT ON REPORTE_FALLA
FOR EACH ROW
BEGIN
    IF NEW.estado_reporte = 'CERRA' THEN
        SET NEW.fechaResolucion = CURRENT_DATE();
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_fecharesolucion_cerrado_update;
DELIMITER $$
CREATE TRIGGER tg_fecharesolucion_cerrado_update
BEFORE UPDATE ON REPORTE_FALLA
FOR EACH ROW
BEGIN
    IF NEW.estado_reporte = 'CERRA' AND (OLD.estado_reporte IS NULL OR OLD.estado_reporte <> 'CERRA') THEN
        SET NEW.fechaResolucion = CURRENT_DATE();
    END IF;
END$$
DELIMITER ;

-- =====================================================================
-- VALIDACIONES DE FECHAS / INTEGRIDAD DE PERIODOS
-- Evitan errores lógicos de fechas a nivel BD (los Serializers de Django
-- dan el mismo mensaje con mejor UX; estos triggers son la red de
-- seguridad para INSERT/UPDATE directos por SQL):
--   * REGISTRO_OPS: un periodo de horas no puede solaparse con otro de
--     la misma máquina (un solapamiento duplica horas en el SUM y el
--     MTBF sale inflado).
--   * INDICADOR: una máquina solo puede tener UN periodo abierto
--     (fechaFin IS NULL); evita periodos huérfanos si alguien inserta
--     por fuera del SP o hay una carrera entre triggers.
--   * INDICADOR: al cerrar un periodo (UPDATE fechaFin) la fecha de fin
--     no puede ser anterior a la de inicio.
-- =====================================================================

DROP TRIGGER IF EXISTS tg_regops_sin_solapamiento_insert;

-- =====================================================================
-- 📍 IMPLEMENTACIÓN EN EL PROYECTO
-- (tg_regops_sin_solapamiento_insert / _update,
--  tg_indicador_unico_periodo_abierto, tg_indicador_fecha_cierre_valida)
--
-- tg_regops_sin_solapamiento_insert -> mismo INSERT del Trigger 1:
--   api/apps/monitoreo/views.py, RegistroOpsAPIView.post (línea 308)
--   POST /monitoreo/maquinas/<codigo>/registro-ops/
--   Frontend: módulo Indicadores -> "Horas de Operación"
--
-- tg_regops_sin_solapamiento_update -> al editar un periodo existente:
--   Archivo: api/apps/monitoreo/views.py
--   Clase:   RegistroOpsUpdateAPIView.patch (línea 324)
--   Endpoint (urls.py): PATCH /monitoreo/registro-ops/<pk>/
--            (name="registro-ops-update")
--
-- tg_indicador_unico_periodo_abierto -> se dispara en cualquier INSERT a
-- INDICADOR, por lo tanto en los mismos puntos que los Triggers 3-4:
--   tg_actualizar_mtbf_registroops / tg_actualizar_mttr_orden (cuando
--   crean un periodo nuevo) y sp_cerrar_periodo_indicador (backend/sp.sql,
--   Procedimiento 1, línea 99: INSERT INTO INDICADOR ...), disparado
--   desde api/apps/indicadores/views.py, CerrarPeriodoIndicadorAPIView
--   (línea 587) -- botón "Cerrar periodo" del módulo Indicadores.
--
-- tg_indicador_fecha_cierre_valida -> se dispara en cualquier UPDATE a
-- INDICADOR que ponga fechaFin, es decir:
--   sp_cerrar_periodo_indicador (backend/sp.sql, línea 95: UPDATE
--   INDICADOR SET fechaFin = fecha_fin ...), mismo botón "Cerrar
--   periodo" mencionado arriba.
-- =====================================================================

DELIMITER $$
CREATE TRIGGER tg_regops_sin_solapamiento_insert
BEFORE INSERT ON REGISTRO_OPS
FOR EACH ROW
BEGIN
    DECLARE solapados INT;

    IF NEW.fechaFin < NEW.fechaInicio THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La fecha de fin no puede ser anterior al inicio del periodo';
    END IF;

    SELECT COUNT(*)
    INTO solapados
    FROM REGISTRO_OPS AS ro
    WHERE ro.maquina = NEW.maquina
      AND NEW.fechaInicio <= ro.fechaFin
      AND ro.fechaInicio <= NEW.fechaFin;

    IF solapados > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El rango de fechas se solapa con otro registro de horas de operacion de la misma maquina';
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_regops_sin_solapamiento_update;
DELIMITER $$
CREATE TRIGGER tg_regops_sin_solapamiento_update
BEFORE UPDATE ON REGISTRO_OPS
FOR EACH ROW
BEGIN
    DECLARE solapados INT;

    IF NEW.fechaFin < NEW.fechaInicio THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La fecha de fin no puede ser anterior al inicio del periodo';
    END IF;

    SELECT COUNT(*)
    INTO solapados
    FROM REGISTRO_OPS AS ro
    WHERE ro.maquina = NEW.maquina
      AND ro.numeroRegistro <> NEW.numeroRegistro
      AND NEW.fechaInicio <= ro.fechaFin
      AND ro.fechaInicio <= NEW.fechaFin;

    IF solapados > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'El rango de fechas se solapa con otro registro de horas de operacion de la misma maquina';
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_indicador_unico_periodo_abierto;
DELIMITER $$
CREATE TRIGGER tg_indicador_unico_periodo_abierto
BEFORE INSERT ON INDICADOR
FOR EACH ROW
BEGIN
    DECLARE abiertos INT;

    IF NEW.fechaFin IS NULL THEN
        SELECT COUNT(*)
        INTO abiertos
        FROM INDICADOR AS i
        WHERE i.maquina = NEW.maquina
          AND i.fechaFin IS NULL;

        IF abiertos > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'La maquina ya tiene un periodo de indicador abierto';
        END IF;
    END IF;
END$$
DELIMITER ;

DROP TRIGGER IF EXISTS tg_indicador_fecha_cierre_valida;
DELIMITER $$
CREATE TRIGGER tg_indicador_fecha_cierre_valida
BEFORE UPDATE ON INDICADOR
FOR EACH ROW
BEGIN
    IF NEW.fechaFin IS NOT NULL AND NEW.fechaFin < NEW.fechaInicio THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'La fecha de fin no puede ser anterior al inicio del periodo';
    END IF;
END$$
DELIMITER ;