from django.db import models
from apps.maquinaria.models import Maquina
from apps.usuarios.models import Trabajador


class TipoSeveridad(models.Model):

    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "TIPO_SEVERIDAD"

    def __str__(self):
        return self.nombre


class TipoFalla(models.Model):

    numeroRegistro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "TIPO_FALLA"

    def __str__(self):
        return self.nombre


class EstadoReporte(models.Model):
    """Mapea la tabla EDO_REPORTE (managed=False)."""

    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "EDO_REPORTE"

    def __str__(self):
        return self.nombre


class Marca(models.Model):
    clave = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "MARCA"

    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    codigo = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    marca = models.ForeignKey(Marca, on_delete=models.DO_NOTHING, db_column="marca")

    class Meta:
        managed = False
        db_table = "MODELO"

    def __str__(self):
        return self.nombre


class TipoMaquina(models.Model):
    numeroRegistro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "TIPO_MAQUINA"

    def __str__(self):
        return self.nombre


class EstadoMaquina(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "EDO_MAQUINA"

    def __str__(self):
        return self.nombre


class Linea(models.Model):
    codigo = models.CharField(max_length=10, primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    area = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = "LINEA"

    def __str__(self):
        return self.nombre


class Maquina(models.Model):


    codigo = models.CharField(max_length=10, primary_key=True)
    numeroSerie = models.CharField(max_length=30, unique=True, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    imagen_url = models.CharField(max_length=255, null=True, blank=True)
    fechaInstalacion = models.DateField()
    linea = models.ForeignKey(
        Linea, on_delete=models.DO_NOTHING, db_column="linea", null=True, blank=True
    )
    marca = models.CharField(max_length=10, null=True, blank=True)
    modelo = models.CharField(max_length=10, null=True, blank=True)
    estado_maquina = models.CharField(max_length=5, null=True, blank=True)
    tipo_maquina = models.IntegerField(null=True, blank=True)
    modo_monitoreo = models.CharField(max_length=10, default="simulado")
    umbral_vibracion = models.FloatField(default=4.0)
    requiere_revision_preventiva = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "MAQUINA"

    def __str__(self):
        return self.nombre


class ReporteFalla(models.Model):

    numeroRegistro = models.AutoField(primary_key=True)
    asunto = models.CharField(max_length=500)
    fechaResolucion = models.DateField(null=True, blank=True)
    fechaCreacion = models.DateField()
    horaCreacion = models.TimeField()
    tiempoParo = models.IntegerField(null=True, blank=True)
    causaRaiz = models.CharField(max_length=500)
    descripcion = models.CharField(max_length=500, null=True, blank=True)
    imagen = models.ImageField(upload_to='fallas_images/')
    maquina = models.ForeignKey(
        Maquina, on_delete=models.DO_NOTHING, db_column="maquina"
    )
    trabajador = models.ForeignKey(
        "usuarios.Trabajador",
        on_delete=models.DO_NOTHING,
        db_column="trabajador",
    )
    tipo_severidad = models.ForeignKey(
        TipoSeveridad,
        on_delete=models.DO_NOTHING,
        db_column="tipo_severidad",
    )
    estado_reporte = models.ForeignKey(
        EstadoReporte,
        on_delete=models.DO_NOTHING,
        db_column="estado_reporte",
        null=True,
        blank=True,
    )

    class Meta:
        managed = False
        db_table = "REPORTE_FALLA"

    def __str__(self):
        return f"{self.numeroRegistro} - {self.asunto}"


class TipoReporte(models.Model):
    tipo_falla = models.ForeignKey(
        TipoFalla, on_delete=models.DO_NOTHING, db_column="tipo_falla"
    )
    reporte_falla = models.ForeignKey(
        ReporteFalla, 
        models.DO_NOTHING, 
        db_column='reporte_falla'
    )

    class Meta:
        managed = False
        db_table = 'tipo_reporte'
        unique_together = (('tipo_falla', 'reporte_falla'),)
