from django.db import models
from apps.maquinaria.models import Maquina
from apps.usuarios.models import Trabajador
from apps.inventario.models import Refaccion, Herramienta
from apps.fallas.models import ReporteFalla

# Create your models here.
class EstadoOrden(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estado_orden'

class TipoMantenimiento(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_mantenimiento'


class Tareas(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    instruccion = models.CharField(max_length=100)
    actividad = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tareas'


class TipoMovimiento(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_movimiento'


class OrdenMantenimiento(models.Model):
    folio = models.CharField(primary_key=True, max_length=15)
    descripcion = models.CharField(max_length=500)
    diagnostico = models.CharField(max_length=500, blank=True, null=True)
    notas = models.CharField(max_length=500, blank=True, null=True)
    fechaprogramada = models.DateField(db_column='fechaProgramada', blank=True, null=True)  # Field name made lowercase.
    fechacreacion = models.DateField(db_column='fechaCreacion')  # Field name made lowercase.
    horacreacion = models.TimeField(db_column='horaCreacion')  # Field name made lowercase.
    fechacierre = models.DateField(db_column='fechaCierre', blank=True, null=True)  # Field name made lowercase.
    horacierre = models.TimeField(db_column='horaCierre', blank=True, null=True)  # Field name made lowercase.
    horasintervenidas = models.FloatField(db_column='horasIntervenidas', blank=True, null=True)  # Field name made lowercase.
    porcentaje = models.FloatField(blank=True, null=True)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    maquina = models.ForeignKey(Maquina, models.DO_NOTHING, db_column='maquina', blank=True, null=True)
    trabajador = models.ForeignKey(Trabajador, models.DO_NOTHING, db_column='trabajador', blank=True, null=True)
    reporte_falla = models.ForeignKey(ReporteFalla, models.DO_NOTHING, db_column='reporte_falla', blank=True, null=True)
    tipo_mantenimiento = models.ForeignKey(TipoMantenimiento, models.DO_NOTHING, db_column='tipo_mantenimiento', blank=True, null=True)
    estado_orden = models.ForeignKey(EstadoOrden, models.DO_NOTHING, db_column='estado_orden', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orden_mantenimiento'

class Movimiento(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    tipomovimiento = models.CharField(db_column='tipoMovimiento', max_length=20)  # Field name made lowercase.
    orden_mantenimiento = models.ForeignKey(OrdenMantenimiento, models.DO_NOTHING, db_column='orden_mantenimiento', blank=True, null=True)
    refaccion = models.ForeignKey(Refaccion, models.DO_NOTHING, db_column='refaccion', blank=True, null=True)
    pieza = models.ForeignKey(Refaccion, models.DO_NOTHING, db_column='PIEZA', related_name='movimiento_pieza_set', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'movimiento'

class TareaOrden(models.Model):
    tarea = models.OneToOneField(Tareas, models.DO_NOTHING, db_column='tarea', primary_key=True)  # The composite primary key (tarea, orden_mantenimiento) found, that is not supported. The first column is selected.
    orden_mantenimiento = models.ForeignKey(OrdenMantenimiento, models.DO_NOTHING, db_column='orden_mantenimiento')
    fechainicio = models.DateField(db_column='fechaInicio')  # Field name made lowercase.
    fechacierre = models.DateField(db_column='fechaCierre', blank=True, null=True)  # Field name made lowercase.
    horainicio = models.TimeField(db_column='horaInicio')  # Field name made lowercase.
    horafin = models.TimeField(blank=True, null=True)
    verificacion = models.IntegerField(blank=True, null=True)
    observaciones = models.CharField(max_length=250, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tarea_orden'
        unique_together = (('tarea', 'orden_mantenimiento'),)

class HerraOrden(models.Model):
    herramienta = models.OneToOneField(Herramienta, models.DO_NOTHING, db_column='herramienta', primary_key=True)  # The composite primary key (herramienta, orden_mantenimiento) found, that is not supported. The first column is selected.
    orden_mantenimiento = models.ForeignKey(OrdenMantenimiento, models.DO_NOTHING, db_column='orden_mantenimiento')

    class Meta:
        managed = False
        db_table = 'herra_orden'
        unique_together = (('herramienta', 'orden_mantenimiento'),)


class TrabaOrdePersonal(models.Model):
    trabajador = models.OneToOneField(Trabajador, models.DO_NOTHING, db_column='trabajador', primary_key=True)  # The composite primary key (trabajador, orden_mantenimiento) found, that is not supported. The first column is selected.
    orden_mantenimiento = models.ForeignKey(OrdenMantenimiento, models.DO_NOTHING, db_column='orden_mantenimiento')

    class Meta:
        managed = False
        db_table = 'traba_orde_personal'
        unique_together = (('trabajador', 'orden_mantenimiento'),)