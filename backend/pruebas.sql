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



-- TRIGER NUMERO 2 PRUEBAS ABAJO CON DATOS 

-- =====================================================
-- PASO 1. Verificar que existan los reportes de falla
-- =====================================================

SELECT numeroRegistro, asunto, tiempoParo, maquina
FROM REPORTE_FALLA
WHERE maquina='MQ001';

-- Deben existir al menos 5 reportes de falla
-- Si realizaste la prueba del MTBF ya deberían existir.

-- =====================================================
-- PASO 2. Crear 5 órdenes de mantenimiento
-- (Todas abiertas, fechaCierre = NULL)
-- =====================================================

INSERT INTO ORDEN_MANTENIMIENTO
(folio, descripcion, fechaProgramada, fechaCreacion, horaCreacion, maquina, reporte_falla)
VALUES 
('OM001','Reparación del motor','2026-01-11','2026-01-10','09:30:00','MQ001',1),
('OM002','Cambio de sensor','2026-02-06','2026-02-05','11:40:00','MQ001',2),
('OM003','Revisión del ventilador','2026-03-04','2026-03-03','13:20:00','MQ001',3),
('OM004','Reparación neumática','2026-04-13','2026-04-12','09:10:00','MQ001',4),
('OM005','Reparación eléctrica','2026-05-21','2026-05-20','15:30:00','MQ001',5);

SELECT folio, fechaCierre
FROM ORDEN_MANTENIMIENTO
WHERE maquina='MQ001';

-- =====================================================
-- PASO 3. Cerrar la orden #1
-- Tiempo paro = 45
-- MTTR esperado = 45
-- =====================================================

UPDATE ORDEN_MANTENIMIENTO
SET fechaCierre='2026-01-11', horaCierre='11:00:00'
WHERE folio='OM001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- =====================================================
-- PASO 4. Cerrar la orden #2
-- Tiempo acumulado = 65
-- Reparaciones = 2
-- MTTR esperado = 32.50
-- =====================================================

UPDATE ORDEN_MANTENIMIENTO
SET fechaCierre='2026-02-06', horaCierre='13:00:00'
WHERE folio='OM002';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- =====================================================
-- PASO 5. Cerrar la orden #3
-- Tiempo acumulado = 120
-- Reparaciones = 3
-- MTTR esperado = 40
-- =====================================================

UPDATE ORDEN_MANTENIMIENTO
SET fechaCierre='2026-03-04', horaCierre='16:00:00'
WHERE folio='OM003';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- =====================================================
-- PASO 6. Cerrar la orden #4
-- Tiempo acumulado = 155
-- Reparaciones = 4
-- MTTR esperado = 38.75
-- =====================================================

UPDATE ORDEN_MANTENIMIENTO
SET fechaCierre='2026-04-13', horaCierre='12:00:00'
WHERE folio='OM004';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- =====================================================
-- PASO 7. Cerrar la orden #5
-- Tiempo acumulado = 215
-- Reparaciones = 5
-- MTTR esperado = 43
-- =====================================================

UPDATE ORDEN_MANTENIMIENTO
SET fechaCierre='2026-05-21', horaCierre='18:00:00'
WHERE folio='OM005';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- =====================================================
-- CONSULTAS FINALES
-- =====================================================

SELECT folio, fechaCierre, horaCierre, reporte_falla
FROM ORDEN_MANTENIMIENTO
WHERE maquina='MQ001';

SELECT numeroRegistro, tiempoParo, maquina
FROM REPORTE_FALLA
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

SELECT SUM(rf.tiempoParo) AS Tiempo_Total_Paro,
COUNT(*) AS Total_Reparaciones, ROUND( SUM(rf.tiempoParo)/COUNT(*),2 ) AS MTTR_Calculado
FROM REPORTE_FALLA rf
INNER JOIN ORDEN_MANTENIMIENTO om
ON rf.numeroRegistro = om.reporte_falla
WHERE om.maquina='MQ001'
AND om.fechaCierre IS NOT NULL;



-- TRIGER NUMERO 3 DATOS PARA PRUEBAS 


-- =====================================================
-- PASO 1. Verificar el indicador de la máquina
-- =====================================================

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- =====================================================
-- PASO 2. Actualizar únicamente el MTBF
-- El trigger detecta el cambio.
-- Como MTTR es NULL, porcentajeDispo seguirá siendo NULL.
-- =====================================================

UPDATE INDICADOR
SET mtbf = 100
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- =====================================================
-- PASO 3. Actualizar el MTTR
-- Ahora existen ambos valores.
-- Se ejecuta nuevamente el trigger.
-- =====================================================

UPDATE INDICADOR
SET mttr = 20
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- Resultado esperado:
--
-- round(100 + 20) * 100
--
-- = 12000

-- =====================================================
-- PASO 4. Cambiar el MTBF
-- =====================================================

UPDATE INDICADOR
SET mtbf = 150
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- Resultado esperado:
--
-- round(150 + 20) *100
--
-- =17000

-- =====================================================
-- PASO 5. Cambiar el MTTR
-- =====================================================

UPDATE INDICADOR
SET mttr = 35
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- Resultado esperado:
--
-- round(150 +35)*100
--
-- =18500

-- =====================================================
-- PASO 6. Cambiar ambos valores
-- =====================================================

UPDATE INDICADOR
SET
mtbf = 200,
mttr = 50
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- Resultado esperado:
--
-- round(250)*100
--
-- =25000

-- =====================================================
-- PASO 7. Colocar MTTR en NULL
-- =====================================================

UPDATE INDICADOR
SET mttr = NULL
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- porcentajeDispo = NULL

-- =====================================================
-- PASO 8. Restaurar el MTTR
-- =====================================================

UPDATE INDICADOR
SET mttr = 40
WHERE maquina='MQ001';

SELECT *
FROM INDICADOR
WHERE maquina='MQ001';

-- Resultado esperado:
--
-- round(200 +40)*100
--
-- =24000

-- =====================================================
-- CONSULTAS FINALES
-- =====================================================

SELECT maquina, mtbf, mttr, porcentajeDispo
FROM INDICADOR
WHERE maquina='MQ001';