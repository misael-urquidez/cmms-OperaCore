-- OperaCore: módulo de monitoreo, fase 1.
-- Ejecutar UNA sola vez sobre la base operacore, después de beta.sql.
-- Este archivo no modifica REGISTRO_OPS ni los triggers existentes.
-- Si ya ejecutaste este archivo antes, no lo corras de nuevo: las columnas
-- y la tabla ya existirán.

ALTER TABLE MAQUINA
    ADD COLUMN modo_monitoreo ENUM('simulado', 'manual', 'iot') NOT NULL DEFAULT 'simulado',
    ADD COLUMN umbral_vibracion FLOAT NOT NULL DEFAULT 4.0,
    ADD COLUMN requiere_revision_preventiva BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE LECTURA_SENSOR (
    numeroRegistro INT AUTO_INCREMENT PRIMARY KEY,
    maquina VARCHAR(10) NOT NULL,
    `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    origen ENUM('manual', 'simulado', 'iot') NOT NULL,
    vibracion FLOAT NOT NULL,
    golpe BOOLEAN NOT NULL DEFAULT FALSE,
    temperatura FLOAT NULL,
    CONSTRAINT fk_lectura_sensor_maquina
        FOREIGN KEY (maquina) REFERENCES MAQUINA(codigo),
    INDEX idx_lectura_sensor_maquina_timestamp (maquina, `timestamp`)
) ENGINE=InnoDB;
