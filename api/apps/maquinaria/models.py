from django.db import models

# Create your models here.
from django.db import models


class Maquina(models.Model):
    codigo = models.CharField(max_length=10, primary_key=True)
    numeroSerie = models.CharField(max_length=30, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    imagen_url = models.CharField(max_length=255, null=True, blank=True)
    fechaInstalacion = models.DateField()

    linea = models.CharField(max_length=10, null=True, blank=True)
    marca = models.CharField(max_length=10, null=True, blank=True)
    modelo = models.CharField(max_length=10, null=True, blank=True)
    estado_maquina = models.CharField(max_length=5, null=True, blank=True)
    tipo_maquina = models.IntegerField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "MAQUINA"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"