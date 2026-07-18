from django.db import models
from apps.maquinaria.models import Maquina
from apps.usuarios.models import Trabajador

# Create your models here.
class TipoFalla(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_falla'


class TipoSeveridad(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=30)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_severidad'

class EdoReporte(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_reporte'

class ReporteFalla(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True) 
    asunto = models.CharField(max_length=500)
    fecharesolucion = models.DateField(db_column='fechaResolucion')  
    fechacreacion = models.DateField(db_column='fechaCreacion')  
    horacreacion = models.TimeField(db_column='horaCreacion')  
    tiempoparo = models.IntegerField(db_column='tiempoParo', blank=True, null=True)  
    causaraiz = models.CharField(db_column='causaRaiz', max_length=500)  
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    maquina = models.ForeignKey(Maquina, models.DO_NOTHING, db_column='maquina', blank=True, null=True)
    trabajador = models.ForeignKey(Trabajador, models.DO_NOTHING, db_column='trabajador', blank=True, null=True)
    tipo_falla = models.ForeignKey(TipoFalla, models.DO_NOTHING, db_column='tipo_falla', blank=True, null=True)
    tipo_severidad = models.ForeignKey(TipoSeveridad, models.DO_NOTHING, db_column='tipo_severidad', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reporte_falla'

class TipoReporte(models.Model):
    tipo_falla = models.OneToOneField(TipoFalla, models.DO_NOTHING, db_column='tipo_falla', primary_key=True)  # The composite primary key (tipo_falla, reporte_falla) found, that is not supported. The first column is selected.
    reporte_falla = models.ForeignKey(ReporteFalla, models.DO_NOTHING, db_column='reporte_falla')

    class Meta:
        managed = False
        db_table = 'tipo_reporte'
        unique_together = (('tipo_falla', 'reporte_falla'),)