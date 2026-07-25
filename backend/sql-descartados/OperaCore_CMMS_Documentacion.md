# OperaCore CMMS — Documentación General del Proyecto

## ¿Qué es este proyecto?

**OperaCore CMMS** es un Sistema Computarizado de Gestión de Mantenimiento Industrial desarrollado para una planta de ensamble de componentes de cómputo (EMS). Su objetivo es gestionar el mantenimiento de 7 máquinas SMT (Surface Mount Technology), controlar el inventario de refacciones y piezas, y generar indicadores de confiabilidad para reducir tiempos de paro no planificados.

El sistema es **exclusivamente de mantenimiento interno** — no gestiona producción, compras externas ni contratos con proveedores de servicio. Esta decisión de alcance es deliberada y está alineada con los CMMS comerciales más populares como UpKeep, Limble y MaintainX, que también están enfocados en mantenimiento interno con personal propio.

---

## Máquinas que gestiona el sistema

| Tipo de máquina | Función |
|---|---|
| Pick & Place | Coloca componentes electrónicos en PCB |
| Horno Reflow | Soldadura de componentes por temperatura |
| AOI | Inspección óptica automatizada |
| Dispensador de pasta | Aplica pasta de soldadura en PCB |
| Transportador | Mueve PCBs entre estaciones |
| Estación de prueba | Verifica funcionamiento de PCBs ensambladas |

---

## Conceptos clave del sistema

### PIEZA vs REFACCION

Esta es la distinción más importante del sistema:

**PIEZA** — componente activo e instalado en la máquina en operación.
- Tiene número de serie único
- Tiene historial de desgaste (horas de operación)
- Se deprecia contablemente
- Pertenece a un nivel del despiece de la máquina

**REFACCION** — componente en reserva en el almacén.
- Tiene stock controlado
- Tiene punto de reorden y stock mínimo
- Viene de un proveedor
- Puede instalarse en la máquina y convertirse en PIEZA

> Un rodamiento puede ser una PIEZA (instalado en el motor) o una REFACCION (guardado en el almacén). Físicamente es el mismo objeto pero el sistema los trata diferente porque tienen ciclos de vida y atributos distintos.

### PLAN vs ORDEN

**PLAN** — plantilla de mantenimiento preventivo. Dice *"cada 30 días lubricar cadenas"*.
- Define qué hacer y cada cuánto
- Tiene disparador por días o por horas de operación
- Genera órdenes automáticamente al cumplirse la condición

**ORDEN** — trabajo real y concreto a ejecutar. Dice *"el 15 de mayo, Juan lubricó cadenas en máquina 3, tardó 2 horas"*.
- Registra quién hizo el trabajo, cuándo y cómo
- Puede nacer de un PLAN (preventivo) o de un REPORTE_FALLA (correctivo)
- Registra refacciones y herramientas usadas

```
PLAN ──origina──► ORDEN (preventivo)
REPORTE_FALLA ──genera──► ORDEN (correctivo)
```

### REPORTE_FALLA vs ORDEN_MANTENIMIENTO

- El **REPORTE_FALLA** documenta qué falló, cuándo y con qué severidad.
- La **ORDEN_MANTENIMIENTO** documenta cómo se atendió esa falla.
- La relación entre ambas es **1:1 opcional** — una orden puede no tener falla asociada (si es preventiva).

### MOVIMIENTO

Entidad que registra la transición de REFACCION a PIEZA y viceversa:

- **Instalación** — una refacción sale del almacén y se instala como pieza en la máquina.
- **Desmontaje** — una pieza se retira de la máquina y puede ir al taller para rehabilitación.
- **Rehabilitación** — una pieza reparada regresa al almacén como refacción disponible.

Todo MOVIMIENTO debe estar asociado a una ORDEN_MANTENIMIENTO para garantizar trazabilidad.

---

## Entidades del sistema (30 en total)

### Módulo Máquinas
| Entidad | Descripción |
|---|---|
| MAQUINA | Equipo industrial registrado en el sistema |
| TIPO_MAQUINA | Catálogo: Pick & Place, Reflow, AOI... |
| MARCA | Fabricante de la máquina (Yamaha, Heller, Omron...) |
| MODELO | Modelo específico de cada marca |
| ESTADO_MAQUINA | Catálogo: Operativa, En mantenimiento, Falla, Baja |
| REGISTRO_OPERACION | Períodos de operación de cada máquina (base para calcular MTBF) |

### Módulo Ubicación
| Entidad | Descripción |
|---|---|
| PLANTA | Instalación física principal |
| LINEA | Línea de producción dentro de la planta |
| AREA | Zona dentro de una línea |
| UBICACION | Punto específico donde está la máquina |

### Módulo Inventario
| Entidad | Descripción |
|---|---|
| PIEZA | Componente instalado y operando en la máquina |
| TIPO_PIEZA | Catálogo: Cabezal, Motor, Sensor... |
| ESTADO_PIEZA | Catálogo: Operativa, En reparación, Baja |
| REFACCION | Componente en almacén disponible para uso |
| TIPO_REFACCION | Catálogo: Filtro, Rodamiento, Sensor, Nozzle... |
| ESTADO_REFACCION | Catálogo: Disponible, Agotada, En pedido |
| CLASIFICACION | Categorización adicional de refacciones |
| PROVEEDOR | Empresa que suministra refacciones |
| MOVIMIENTO | Registro de conversiones entre PIEZA y REFACCION |
| TIPO_MOVIMIENTO | Catálogo: Instalación, Desmontaje, Rehabilitación |

### Módulo Fallas
| Entidad | Descripción |
|---|---|
| REPORTE_FALLA | Registro de una falla en una máquina |
| TIPO_FALLA | Catálogo: Mecánica, Eléctrica, Neumática, Software, Óptica |
| TIPO_SEVERIDAD | Catálogo: Crítica, Alta, Media, Baja |
| ESTADO_REPORTE | Catálogo: Abierto, En atención, Resuelto, Cerrado |

### Módulo Órdenes
| Entidad | Descripción |
|---|---|
| ORDEN_MANTENIMIENTO | Trabajo de mantenimiento ejecutado o por ejecutar |
| TIPO_MANTENIMIENTO | Catálogo: Preventivo, Correctivo, Predictivo, Emergencia |
| ESTADO_ORDEN | Catálogo: Pendiente, En proceso, Cerrada, Cancelada |
| TAREAS | Pasos del checklist dentro de una orden |
| HERRAMIENTA | Herramienta usada en la ejecución de una orden |
| TIPO_HERRAMIENTA | Catálogo de tipos de herramientas |
| PLAN | Plan de mantenimiento preventivo programado |

### Módulo Personal
| Entidad | Descripción |
|---|---|
| TRABAJADOR | Técnico o encargado registrado en el sistema |
| ROL | Catálogo: Administrador, Encargado de línea, Técnico |
| ESPECIALIDAD | Certificaciones del técnico (SMT, BGA, AOI...) |

### Módulo Indicadores
| Entidad | Descripción |
|---|---|
| INDICADOR | Métricas de confiabilidad calculadas por período por máquina |

---

## Indicadores de confiabilidad

### MTBF — Tiempo Medio Entre Fallas
```
MTBF = horas_operacion_del_periodo / numero_fallas
```
Fuente de datos: REGISTRO_OPERACION + conteo de REPORTE_FALLA del período.

Ejemplo: La Pick & Place operó 208 horas en enero y tuvo 2 fallas → MTBF = 104 horas.

### MTTR — Tiempo Medio de Reparación
```
MTTR = suma(tiempo_paro_hrs) / numero_reparaciones
```
Fuente de datos: suma de tiempo_paro_hrs de REPORTE_FALLA + conteo de ORDEN_MANTENIMIENTO cerradas del período.

Ejemplo: Las 2 fallas sumaron 5 horas de paro y hubo 2 reparaciones → MTTR = 2.5 horas.

### Disponibilidad
```
porcentajeDisponibilidad = (MTBF / (MTBF + MTTR)) × 100
```
Ejemplo: (104 / (104 + 2.5)) × 100 = 97.65%

> Estos tres valores son **atributos calculados** — se derivan de otras tablas y se guardan en INDICADOR por período para mantener historial y poder analizar tendencias.

---

## Atributos importantes y por qué existen

### En PIEZA
| Atributo | Tipo | Descripción |
|---|---|---|
| numero_serie | Normal | Identificador físico único de esa pieza instalada |
| fecha_instalacion | Normal | Cuándo se instaló en la máquina |
| vida_util | Normal | Tiempo estimado de duración (viene del fabricante) |
| costo_inicial | Normal | Lo que costó cuando se instaló |
| valor_residual | Normal | Lo que valdría al final de su vida útil (define contabilidad) |
| depreciacion_anual | Calculado | (costo_inicial - valor_residual) / vida_util |
| codigo_etiqueta | Normal | Código físico pegado en la pieza |
| pieza_padre_id | FK recursiva | Para el despiece jerárquico de la máquina |

### En REFACCION
| Atributo | Tipo | Descripción |
|---|---|---|
| stock | Normal | Unidades disponibles actualmente |
| stock_minimo | Normal | Cantidad mínima aceptable antes de alerta |
| punto_reorden | Normal | Cantidad en la que se debe hacer el pedido |
| tiempo_entrega | Normal | Días que tarda en llegar del proveedor |
| ubicacion_almacen | Normal | Dónde está físicamente en el almacén |

### En INDICADOR
| Atributo | Tipo | Descripción |
|---|---|---|
| fecha_inicio_periodo | Normal | Desde cuándo se calculó |
| fecha_fin_periodo | Normal | Hasta cuándo se calculó |
| mtbf | Calculado | Horas entre fallas del período |
| mttr | Calculado | Horas promedio de reparación del período |
| porcentajeDisponibilidad | Calculado | Derivado de mtbf y mttr |

### En MAQUINA
| Atributo | Tipo | Descripción |
|---|---|---|
| horas_operacion | Calculado | Odómetro acumulado desde instalación — suma desde REGISTRO_OPERACION |
| numero_serie | Normal | Identificador físico único |
| imagen_url | Normal | Foto del equipo |

---

## Normalización aplicada

### Primera Forma Normal (1FN)
- Todas las entidades tienen llave primaria (numero_registro)
- Todos los atributos son atómicos — un solo valor por campo

### Segunda Forma Normal (2FN)
- Todos los atributos dependen completamente de la llave primaria
- No existen dependencias parciales

### Tercera Forma Normal (3FN)
- Los datos se relacionan mediante FK en lugar de duplicarse
- Se crearon entidades separadas para MARCA y MODELO para evitar dependencias transitivas en MAQUINA
- `horas_operacion` se calcula desde REGISTRO_OPERACION en lugar de guardarse directamente
- `porcentajeDisponibilidad` es atributo calculado porque se deriva de mtbf y mttr

---

## Cardinalidades importantes

| Relación | Cardinalidad | Justificación |
|---|---|---|
| MAQUINA — ORDEN | 1:M | Una máquina tiene muchas órdenes, una orden es de una sola máquina |
| REPORTE_FALLA — ORDEN | 1:1 opcional | Una falla genera como máximo una orden correctiva |
| TRABAJADOR — ORDEN (levanta) | 1:M | Un trabajador levanta muchas órdenes, una orden la levanta un solo trabajador |
| TRABAJADOR — ORDEN (participan) | M:M | Varios trabajadores pueden participar en una orden |
| ORDEN — TAREAS | M:M | Una orden tiene varias tareas, una tarea puede repetirse en varias órdenes |
| PIEZA — REFACCION (es compatible) | M:M | Una pieza puede ser sustituida por varias refacciones y viceversa |
| PROVEEDOR — REFACCION | 1:M | Un proveedor surte muchas refacciones, una refacción tiene un proveedor principal |
| MAQUINA — INDICADOR | 1:M | Una máquina genera muchos indicadores (uno por período) |
| MOVIMIENTO — PIEZA | M:1 | Una pieza puede tener muchos movimientos históricos |
| MOVIMIENTO — REFACCION | M:1 | Una refacción puede tener muchos movimientos históricos |
| PLANTA — LINEA — AREA — UBICACION — MAQUINA | Jerárquica 1:M | Cada nivel contiene al siguiente |

---

## Ciclo de vida de una refacción

```
PROVEEDOR ──provee──► REFACCION (en almacén)
                           │
                    ORDEN_MANTENIMIENTO
                    (MOVIMIENTO tipo instalación)
                           │
                           ▼
                    PIEZA (instalada en MAQUINA)
                           │
                    ORDEN_MANTENIMIENTO
                    (MOVIMIENTO tipo desmontaje)
                           │
                           ▼
                    Taller de rehabilitación
                    (ESTADO_PIEZA = en rehabilitación)
                           │
                    (MOVIMIENTO tipo rehabilitación)
                           │
                           ▼
                    REFACCION (vuelve al almacén con stock +1)
```

---

## Consumibles vs Refacciones

No todos los insumos del almacén se instalan como piezas. Algunos se consumen directamente durante el mantenimiento:

**Consumibles** (no se convierten en PIEZA):
- Lubricantes y grasas
- Alcohol isopropílico
- Pasta de soldadura
- Flux de limpieza
- Paños industriales

**Refacciones instalables** (se convierten en PIEZA):
- Rodamientos
- Motores servo
- Sensores ópticos
- Nozzles
- Correas de transmisión

> Decisión de diseño: el sistema solo gestiona refacciones instalables. Los consumibles quedan fuera del alcance porque su gestión no implica montaje/desmontaje de componentes.

---

## Flujo completo de una falla

```
1. Técnico detecta falla en máquina
2. Crea REPORTE_FALLA (asunto, descripción, tipo, severidad)
3. Sistema calcula tiempo_paro_hrs = fecha_resolucion - fecha_creacion
4. Se crea ORDEN_MANTENIMIENTO correctiva vinculada al reporte
5. Se asigna TRABAJADOR a la orden
6. Se asignan HERRAMIENTAS necesarias
7. Si se requiere refacción:
   - Se crea MOVIMIENTO tipo "instalación"
   - Stock de REFACCION disminuye
   - Se crea nuevo registro en PIEZA
   - Si stock llega a punto_reorden → alerta de reorden
8. Técnico ejecuta TAREAS del checklist
9. Se registra diagnóstico y notas
10. ORDEN se cierra → ESTADO_ORDEN = Cerrada
11. MAQUINA vuelve a ESTADO_MAQUINA = Operativa
12. Al cierre del período → sistema calcula INDICADOR
```

---

## Requerimientos funcionales principales

| Código | Descripción |
|---|---|
| RF-01 | Registro de maquinaria |
| RF-02 | Actualización de datos de maquinaria |
| RF-03 | Consulta de maquinaria |
| RF-04 | Captura de horas de operación |
| RF-05 | Creación de tipos de máquina |
| RF-22 | Cálculo de MTBF, MTTR y disponibilidad |
| RF-27 | Registro de reportes de falla |
| RF-31 | Clasificación de falla por severidad |
| RF-43 | Registro de órdenes de mantenimiento |
| RF-44 | Edición de órdenes |
| RF-45 | Consulta de órdenes |
| RF-50 | Calendario de órdenes de mantenimiento |
| RF-58 | Verificación de checklist de tareas |
| RF-69 | Inventario de refacciones |
| RF-76 | Control de stock |
| RF-78 | Alerta de stock bajo |
| RF-90 | Registro de personal técnico |
| RF-93 | Registro de especialidades técnicas |
| RF-98 | Gestión de alertas y notificaciones |

---

## Requerimientos no funcionales

| Código | Descripción | Categoría | Prioridad |
|---|---|---|---|
| RNF-04 | Disponibilidad continua durante horario de operación | Disponibilidad | Urgente/Importante |
| RNF-06 | Datos mostrados en menos de 5 segundos | Performance | Importante/No urgente |
| RNF-07 | Bloqueo de operaciones según estado de la máquina | Seguridad | Urgente/No importante |
| RNF-08 | Cierre de sesión por inactividad (15 min) | Seguridad | Importante/No urgente |
| RNF-11 | Restricción de acceso por rol (RBAC) | Seguridad | Urgente/Importante |
| RNF-12 | Sistema responsivo a cualquier tamaño de pantalla | Usabilidad | Urgente/Importante |
| RNF-14 | Escalabilidad sin afectar rendimiento | Escalabilidad | Importante/No urgente |
| RNF-15 | Portabilidad a dispositivos móviles WebView | Compatibilidad | Importante/No urgente |
| RNF-16 | Fiabilidad en manejo y almacenamiento de datos | Fiabilidad | Urgente/Importante |
| RNF-18 | Exportación a PDF/CSV e interoperabilidad | Interoperabilidad | Urgente/No importante |
| RNF-19 | Mensajes de retroalimentación tipo toast | Confiabilidad | Urgente/No importante |
| RNF-20 | Ventana de confirmación para eliminar maquinaria | Confiabilidad | Importante/No urgente |
| RNF-22 | Validación de tipos de datos en formularios | Usabilidad | Urgente/Importante |

---

## Roles del sistema

| Rol | Permisos |
|---|---|
| Administrador | Acceso total al sistema |
| Encargado de línea | Registro y actualización de maquinaria, validación de órdenes |
| Técnico | Levantamiento de reportes, ejecución y cierre de órdenes asignadas |

---

## Decisiones de diseño importantes

**¿Por qué PIEZA y REFACCION son entidades separadas?**
Porque tienen atributos completamente distintos. Unificarlas generaría valores nulos masivos y violaría la normalización. Una pieza instalada necesita horas_operacion y depreciacion; una refacción en almacén necesita stock y punto_reorden.

**¿Por qué no se relaciona PROVEEDOR con MAQUINA?**
Porque el sistema gestiona mantenimiento, no adquisiciones. Las máquinas ya están instaladas. PROVEEDOR solo es relevante para reabastecer refacciones.

**¿Por qué INDICADOR es una entidad separada y no atributos de MAQUINA?**
Porque guardar MTBF y MTTR en MAQUINA solo daría el valor más reciente. INDICADOR guarda un registro por período, permitiendo analizar tendencias y comparar el comportamiento mes a mes.

**¿Por qué el sistema es solo de mantenimiento interno?**
El alcance está definido para la planta específica con personal propio. Agregar mantenimiento externo requeriría módulos de contratos, SLAs y facturación — fuera del alcance. El modelo es extensible para agregar esto en versiones futuras sin modificar la estructura actual.

**¿Por qué se eliminó la relación REFACCION — ORDEN?**
Porque el uso de refacciones en una orden ahora queda registrado en MOVIMIENTO con mayor detalle y trazabilidad. Los consumibles (lubricantes, solventes) quedaron fuera del alcance porque no implican montaje/desmontaje.

---

## Glosario

| Término | Definición |
|---|---|
| CMMS | Sistema Computarizado de Gestión de Mantenimiento |
| SMT | Surface Mount Technology — tecnología de montaje superficial de componentes electrónicos |
| PCB | Printed Circuit Board — tarjeta de circuito impreso |
| MTBF | Mean Time Between Failures — Tiempo Medio Entre Fallas |
| MTTR | Mean Time To Repair — Tiempo Medio de Reparación |
| Disponibilidad | Porcentaje del tiempo que la máquina estuvo operativa |
| Despiece | Estructura jerárquica de componentes de una máquina |
| Punto de reorden | Cantidad de stock en la que se debe hacer un nuevo pedido |
| Stock mínimo | Cantidad mínima aceptable en almacén antes de generar alerta |
| Valor residual | Valor estimado de un activo al final de su vida útil |
| RBAC | Role Based Access Control — Control de acceso basado en roles |
| EMS | Electronics Manufacturing Services — Servicios de manufactura electrónica |
| Tabla intermedia | Tabla generada por una relación M:M en base de datos relacional |
| Atributo calculado | Atributo que se deriva de otros datos y no se introduce manualmente |
