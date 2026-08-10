from django.db import models

from apps.fallas.models import Maquina, ReporteFalla


class LecturaSensor(models.Model):
    ORIGEN_MANUAL = "manual"
    ORIGEN_SIMULADO = "simulado"
    ORIGEN_IOT = "iot"
    ORIGENES = (
        (ORIGEN_MANUAL, "Manual"),
        (ORIGEN_SIMULADO, "Simulado"),
        (ORIGEN_IOT, "IoT"),
    )

    numeroRegistro = models.AutoField(primary_key=True)
    maquina = models.ForeignKey(Maquina, on_delete=models.DO_NOTHING, db_column="maquina")
    timestamp = models.DateTimeField()
    origen = models.CharField(max_length=10, choices=ORIGENES)
    vibracion = models.FloatField()
    golpe = models.BooleanField(default=False)
    temperatura = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "LECTURA_SENSOR"
        ordering = ["-timestamp"]


class Indicador(models.Model):
    numeroRegistro = models.AutoField(primary_key=True)
    fechaInicio = models.DateField(null=True, blank=True)
    fechaFin = models.DateField(null=True, blank=True)
    mttr = models.FloatField(null=True, blank=True)
    mtbf = models.FloatField(null=True, blank=True)
    porcentajeDispo = models.IntegerField(null=True, blank=True)
    maquina = models.ForeignKey(Maquina, on_delete=models.DO_NOTHING, db_column="maquina", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "INDICADOR"


class IndicadorActual(models.Model):
    """Último periodo de INDICADOR por máquina más los datos de origen de
    las fórmulas (total horas operación, fallas, paro y reparaciones),
    calculados en vivo desde la vista `v_kpi_indicadores_actuales`
    (backend/vistas_kpi.sql). Solo lectura."""

    Codigo = models.CharField(primary_key=True, max_length=10)
    Maquina = models.CharField(max_length=100)
    Estado = models.CharField(max_length=50, null=True, blank=True)
    Linea = models.CharField(max_length=50, null=True, blank=True)
    MTTR = models.FloatField(null=True, blank=True)
    MTBF = models.FloatField(null=True, blank=True)
    Disponibilidad = models.IntegerField(null=True, blank=True)
    Periodo = models.DateField(null=True, blank=True)
    TotalHorasOperacion = models.IntegerField(null=True, blank=True)
    TotalFallas = models.IntegerField(null=True, blank=True)
    TiempoTotalParo = models.IntegerField(null=True, blank=True)
    NumReparaciones = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "v_kpi_indicadores_actuales"


class TipoMantenimiento(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = "TIPO_MANTENIMIENTO"


class EstadoOrden(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = "ESTADO_ORDEN"


class OrdenMantenimiento(models.Model):
    folio = models.CharField(max_length=15, primary_key=True)
    descripcion = models.CharField(max_length=500)
    fechaCreacion = models.DateField()
    horaCreacion = models.TimeField()
    maquina = models.ForeignKey(Maquina, on_delete=models.DO_NOTHING, db_column="maquina", null=True, blank=True)
    trabajador = models.ForeignKey("usuarios.Trabajador", on_delete=models.DO_NOTHING, db_column="trabajador", null=True, blank=True)
    reporte_falla = models.ForeignKey(ReporteFalla, on_delete=models.DO_NOTHING, db_column="reporte_falla", null=True, blank=True)
    tipo_mantenimiento = models.ForeignKey(TipoMantenimiento, on_delete=models.DO_NOTHING, db_column="tipo_mantenimiento", null=True, blank=True)
    estado_orden = models.ForeignKey(EstadoOrden, on_delete=models.DO_NOTHING, db_column="estado_orden", null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ORDEN_MANTENIMIENTO"


class RegistroOps(models.Model):
    """Periodo de horas de operación de una máquina. Cada INSERT aquí
    dispara el trigger `tg_actualizar_mtbf_registroops`, que recalcula
    el MTBF de la máquina y actualiza INDICADOR (y en cascada, mediante
    `tg_actualizar_disponibilidad_indicador`, la disponibilidad)."""

    numeroRegistro = models.AutoField(primary_key=True)
    fechaInicio = models.DateField()
    fechaFin = models.DateField()
    horasOperacion = models.IntegerField()
    maquina = models.ForeignKey(Maquina, on_delete=models.DO_NOTHING, db_column="maquina")

    class Meta:
        managed = False
        db_table = "REGISTRO_OPS"
