----------- triggers del proyecto -------------

/*
Trigger 1 
Este trigger recalcula el MTBF de la máquina a la que pertenece el nuevo registro.

*/

use operacore;

SELECT * from registro_ops;

DELIMITER $$

create or REPLACE TRIGGER tg_actualizar_mtbf_registroops
AFTER INSERT ON REGISTRO_OPS
FOR EACH ROW
BEGIN

    DECLARE totalhoras INT;
    DECLARE totalfallas INT;
    DECLARE nuevomtbf FLOAT;


    -- horas totales de operacion de la maquina

    SELECT sum(horasoperacion)


