UPDATE maquina
SET
    numeroSerie = 'SN-YAM-YPK2-001',
    nombre = 'Pick & Place Principal',
    descripcion = 'Máquina de alta velocidad para colocación de componentes SMT',
    imagen_url = 'images/YamahaYS12.png',
    fechaInstalacion = '2020-01-15',
    linea = 'LI001',
    marca = 'YAMHA',
    modelo = 'YPK2',
    estado_maquina = 'OPERA',
    tipo_maquina = '1',
    modelo_3d = 'images/YamahaYS12.glb'
WHERE codigo = 'MAQ001';

UPDATE maquina
SET
    numeroSerie = 'SN-HEL-HLR6-001',
    nombre = 'Horno Reflow',
    descripcion = 'Horno de reflow con 6 zonas de temperatura para soldadura',
    imagen_url = 'images/Heller1707MK5.png',
    fechaInstalacion = '2019-06-20',
    linea = 'LI001',
    marca = 'HELR',
    modelo = 'HLR6',
    estado_maquina = 'OPERA',
    tipo_maquina = '2',
    modelo_3d = 'images/Heller1707MK5.glb'
WHERE codigo = 'MAQ002';

UPDATE maquina
SET
    numeroSerie = 'SN-OMR-VTS-001',
    nombre = 'AOI Inspector',
    descripcion = 'Sistema de inspección óptica automatizada 3D',
    imagen_url = 'images/KohYoungZenithAlpha3D.png',
    fechaInstalacion = '2021-03-10',
    linea = 'LI002',
    marca = 'OMRN',
    modelo = 'VT-S',
    estado_maquina = 'MANTE',
    tipo_maquina = '3',
    modelo_3d = 'images/KohYoungZenithAlpha3D.glb'
WHERE codigo = 'MAQ003';

UPDATE maquina
SET
    numeroSerie = 'SN-DMD-TFS6-001',
    nombre = 'Dispensador de Pasta',
    descripcion = 'Dispensador de pasta de soldadura de alto volumen',
    imagen_url = 'images/DEKNeoHorizon03iX.png',
    fechaInstalacion = '2020-08-05',
    linea = 'LI001',
    marca = 'DMDE',
    modelo = 'TFS6',
    estado_maquina = 'OPERA',
    tipo_maquina = '4',
    modelo_3d = 'images/DEKNeoHorizon03iX.glb'
WHERE codigo = 'MAQ004';

UPDATE maquina
SET
    numeroSerie = 'SN-BRN-CONV-001',
    nombre = 'Transportador Principal',
    descripcion = 'Transportador de banda continua entre estaciones',
    imagen_url = 'images/JOTAutomationJ301-10.png',
    fechaInstalacion = '2018-11-12',
    linea = 'LI001',
    marca = 'BRNS',
    modelo = 'CONV1',
    estado_maquina = 'OPERA',
    tipo_maquina = '5',
    modelo_3d = 'images/JOTAutomationJ301-10.glb'
WHERE codigo = 'MAQ005';

UPDATE maquina
SET
    numeroSerie = 'SN-KEY-DMM3-001',
    nombre = 'Estación de Prueba',
    descripcion = 'Estación de prueba multicanal para verificación de PCBs',
    imagen_url = 'images/SeicaPilotV8.png',
    fechaInstalacion = '2022-02-28',
    linea = 'LI002',
    marca = 'KYWR',
    modelo = 'DMM3',
    estado_maquina = 'FALLO',
    tipo_maquina = '6',
    modelo_3d = 'images/SeicaPilotV8.glb'
WHERE codigo = 'MAQ006';