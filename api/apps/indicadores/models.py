from django.db import models
from apps.maquinaria.models import Maquina

# Create your models here.
class Indicador(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    fechainicio = models.DateField(db_column='fechaInicio', blank=True, null=True)  # Field name made lowercase.
    fechafin = models.DateField(db_column='fechaFin', blank=True, null=True)  # Field name made lowercase.
    mttr = models.FloatField(blank=True, null=True)
    mtbf = models.FloatField(blank=True, null=True)
    porcentajedispo = models.IntegerField(db_column='porcentajeDispo', blank=True, null=True)  # Field name made lowercase.
    maquina = models.ForeignKey(Maquina, models.DO_NOTHING, db_column='maquina', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'indicador'