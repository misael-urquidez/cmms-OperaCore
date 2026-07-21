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
