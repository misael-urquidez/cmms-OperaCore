-- OperaCore: fix de TIPO_REPORTE (rama fix-sql).
-- Ejecutar UNA sola vez, solo si tu base ya existia ANTES de este fix
-- (o sea, si tu TIPO_REPORTE todavia tiene PRIMARY KEY (tipo_falla, reporte_falla)
-- y no tiene columna `id`). Si vas a crear la base desde cero con beta.sql,
-- no necesitas este archivo: ya viene incluido ahi.

ALTER TABLE TIPO_REPORTE
    DROP PRIMARY KEY,
    ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST,
    ADD UNIQUE KEY uq_tiporep_falla_reporte (tipo_falla, reporte_falla);
