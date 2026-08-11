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

ALTER TABLE REFACCION
    MODIFY codigoInventario VARCHAR(30) NULL UNIQUE,
    MODIFY numeroOrden      VARCHAR(20) NULL UNIQUE;
