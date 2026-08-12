-- =====================================================================
-- ALTERACIONES EVOLUTIVAS (aplicar sobre una BD ya creada con beta4.sql)
-- =====================================================================
--
-- REFACCION: codigoInventario y numeroOrden pasan a NULL. Motivo: una
-- refaccion creada al vuelo durante un REHA (rehabilitacion de pieza)
-- no tiene inventario/orden de compra; esos datos se rellenan despues
-- en la ficha del catalogo si aplican.
-- =====================================================================

USE operacore;

-- =====================================================================
-- HERRAMIENTA: nueva columna stock. A diferencia de REFACCION (que tiene
-- triggers que mantienen stock = SUMA de ESTADO_*), HERRAMIENTA no tiene
-- triggers: la invariante se replica en Python (apps/inventario/stock.py)
-- al crear/editar la herramienta, al asignarla a una orden (DISPO -> ENUSO)
-- y al liberarla al cerrar/cancelar (ENUSO -> DISPO).
-- =====================================================================

ALTER TABLE HERRAMIENTA
    ADD COLUMN stock INT NOT NULL DEFAULT 0;

-- Backfill con los totales ya existentes en la M:M ESTADO_HERRAMIENTA.
UPDATE HERRAMIENTA h
    LEFT JOIN (SELECT herramienta, SUM(cantidad) AS total
               FROM ESTADO_HERRAMIENTA GROUP BY herramienta) e
        ON e.herramienta = h.numeroRegistro
SET h.stock = COALESCE(e.total, 0);

ALTER TABLE REFACCION
    MODIFY codigoInventario VARCHAR(30) NULL UNIQUE,
    MODIFY numeroOrden      VARCHAR(20) NULL UNIQUE;
