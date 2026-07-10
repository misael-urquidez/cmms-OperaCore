USE operacore;

-- =====================================================
-- PASO 1. Verificar que exista la máquina
-- =====================================================

SELECT * FROM MAQUINA WHERE codigo='MQ001';

-- Si no existe, descomenta este INSERT

/*
INSERT INTO MAQUINA
(codigo,numeroSerie,nombre,descripcion,fechaInstalacion)
VALUES ('MQ001','SER0001','Pick And Place 1','Máquina para pruebas del trigger MTBF','2025-01-01');

*/

-- =====================================================
-- PASO 2. Insertar 5 fallas
-- =====================================================

INSERT INTO REPORTE_FALLA
(asunto,fechaResolucion,fechaCreacion,horaCreacion,tiempoParo,causaRaiz,descripcion,maquina)
VALUES
('Motor detenido','2026-01-11','2026-01-10','09:00:00',45,'Desgaste','Motor principal detenido','MQ001'),
('Sensor óptico','2026-02-06','2026-02-05','11:30:00',20,'Suciedad','No detecta piezas','MQ001'),
('Sobrecalentamiento','2026-03-04','2026-03-03','13:15:00',55,'Ventilador dañado','Temperatura elevada','MQ001'),
('Error neumático','2026-04-13','2026-04-12','08:40:00',35,'Fuga de aire','Presión insuficiente','MQ001'),
('Falla eléctrica','2026-05-21','2026-05-20','15:20:00',60,'Corto circuito','Paro total','MQ001');

SELECT COUNT(*) AS Total_Fallas
FROM REPORTE_FALLA
WHERE maquina='MQ001';

-- =====================================================
-- PASO 3. Registro de operación #1
-- Horas = 80
-- MTBF esperado = 16
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-01-01','2026-01-31',80,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 4. Registro #2
-- Horas acumuladas = 200
-- MTBF esperado = 40
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-02-01','2026-02-28',120,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 5. Registro #3
-- Horas acumuladas = 295
-- MTBF esperado = 59
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-03-01','2026-03-31',95,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 6. Registro #4
-- Horas acumuladas = 435
-- MTBF esperado = 87
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-04-01','2026-04-30',140,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 7. Registro #5
-- Horas acumuladas = 535
-- MTBF esperado = 107
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-05-01','2026-05-31',100,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 8. Registro #6
-- Horas acumuladas = 695
-- MTBF esperado = 139
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-06-01','2026-06-30',160,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 9. Registro #7
-- Horas acumuladas = 805
-- MTBF esperado = 161
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-07-01','2026-07-31',110,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 10. Registro #8
-- Horas acumuladas = 895
-- MTBF esperado = 179
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-08-01','2026-08-31',90,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 11. Registro #9
-- Horas acumuladas = 1025
-- MTBF esperado = 205
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-09-01','2026-09-30',130,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- PASO 12. Registro #10
-- Horas acumuladas = 1175
-- MTBF esperado = 235
-- =====================================================

INSERT INTO REGISTRO_OPS (fechaInicio,fechaFin,horasOperacion,maquina)
VALUES ('2026-10-01','2026-10-31',150,'MQ001');

SELECT * FROM INDICADOR WHERE maquina='MQ001';

-- =====================================================
-- CONSULTAS FINALES
-- =====================================================

SELECT * FROM REGISTRO_OPS
WHERE maquina='MQ001';

SELECT * FROM REPORTE_FALLA
WHERE maquina='MQ001';

SELECT * FROM INDICADOR
WHERE maquina='MQ001';

SELECT
    maquina,
    SUM(horasOperacion) AS Horas_Totales,
    (
        SELECT COUNT(*)
        FROM REPORTE_FALLA rf
        WHERE rf.maquina = ro.maquina
    ) AS Total_Fallas,
    ROUND(
        SUM(horasOperacion) /
        (
            SELECT COUNT(*)
            FROM REPORTE_FALLA rf
            WHERE rf.maquina = ro.maquina
        ),
        2
    ) AS MTBF_Calculado
FROM REGISTRO_OPS ro
GROUP BY maquina;