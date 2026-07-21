from django.db import models
from apps.maquinaria.models import Maquina

# Create your models here.
class Clasificacion(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'clasificacion'


class EdoHerramienta(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_herramienta'

class EdoPieza(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_pieza'


class EdoRefaccion(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_refaccion'

class TipoHerramienta(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_herramienta'

class TipoPieza(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_pieza'

class TipoRefaccion(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_refaccion'

class Proveedor(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    rfc = models.CharField(unique=True, max_length=13)
    razonsocial = models.CharField(db_column='razonSocial', unique=True, max_length=100)  # Field name made lowercase.
    nombrecomercial = models.CharField(db_column='nombreComercial', unique=True, max_length=100)  # Field name made lowercase.
    telefono = models.CharField(unique=True, max_length=15)
    email = models.CharField(unique=True, max_length=100)
    dircalle = models.CharField(db_column='dirCalle', max_length=100)  # Field name made lowercase.
    dircodigopostal = models.CharField(db_column='dirCodigoPostal', max_length=5)  # Field name made lowercase.
    dirnumero = models.CharField(db_column='dirNumero', max_length=10)  # Field name made lowercase.
    contnombre = models.CharField(db_column='contNombre', max_length=50)  # Field name made lowercase.
    contapellpat = models.CharField(db_column='contApellPat', max_length=50)  # Field name made lowercase.
    contapellmat = models.CharField(db_column='contApellMat', max_length=50, blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'proveedor'

class Herramienta(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    tipo_herramienta = models.ForeignKey(TipoHerramienta, models.DO_NOTHING, db_column='tipo_herramienta', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'herramienta'

class Pieza(models.Model):
    numeroserie = models.CharField(db_column='numeroSerie', primary_key=True, max_length=30)  # Field name made lowercase.
    codigoetiqueta = models.CharField(db_column='codigoEtiqueta', unique=True, max_length=30, blank=True, null=True)  # Field name made lowercase.
    nombre = models.CharField(max_length=100)
    costoinicial = models.FloatField(db_column='costoInicial')  # Field name made lowercase.
    horasoperacion = models.IntegerField(db_column='horasOperacion')  # Field name made lowercase.
    tiempovidautil = models.IntegerField(db_column='tiempoVidaUtil')  # Field name made lowercase.
    depresacionanual = models.FloatField(db_column='depresacionAnual', blank=True, null=True)  # Field name made lowercase.
    valorresidual = models.FloatField(db_column='valorResidual', blank=True, null=True)  # Field name made lowercase.
    fechainstalacion = models.DateField(db_column='fechaInstalacion')  # Field name made lowercase.
    fechagarantia = models.DateField(db_column='fechaGarantia', blank=True, null=True)  # Field name made lowercase.
    edo_pieza = models.ForeignKey(EdoPieza, models.DO_NOTHING, db_column='edo_pieza', blank=True, null=True)
    maquina = models.ForeignKey(Maquina, models.DO_NOTHING, db_column='maquina', blank=True, null=True)
    tipo_pieza = models.ForeignKey(TipoPieza, models.DO_NOTHING, db_column='tipo_pieza', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pieza'


class Refaccion(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=30)
    codigosku = models.CharField(db_column='codigoSku', unique=True, max_length=30)  # Field name made lowercase.
    puntoreorden = models.IntegerField(db_column='puntoReorden', blank=True, null=True)  # Field name made lowercase.
    codigoinventario = models.CharField(db_column='codigoInventario', unique=True, max_length=30)  # Field name made lowercase.
    numeroorden = models.CharField(db_column='numeroOrden', unique=True, max_length=20)  # Field name made lowercase.
    costo = models.FloatField()
    tiempoentregaapr = models.IntegerField(db_column='tiempoEntregaApr', blank=True, null=True)  # Field name made lowercase.
    stock = models.IntegerField()
    stockminimo = models.IntegerField(db_column='stockMinimo')  # Field name made lowercase.
    proveedor = models.ForeignKey(Proveedor, models.DO_NOTHING, db_column='proveedor', blank=True, null=True)
    tipo_refaccion = models.ForeignKey(TipoRefaccion, models.DO_NOTHING, db_column='tipo_refaccion', blank=True, null=True)
    clasificacion = models.ForeignKey(Clasificacion, models.DO_NOTHING, db_column='clasificacion', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'refaccion'

class RefaccMaqui(models.Model):
    maquina = models.OneToOneField(Maquina, models.DO_NOTHING, db_column='maquina', primary_key=True)  # The composite primary key (maquina, refaccion) found, that is not supported. The first column is selected.
    refaccion = models.ForeignKey(Refaccion, models.DO_NOTHING, db_column='refaccion')

    class Meta:
        managed = False
        db_table = 'refacc_maqui'
        unique_together = (('maquina', 'refaccion'),)

class EstadoHerramienta(models.Model):
    herramienta = models.OneToOneField(Herramienta, models.DO_NOTHING, db_column='herramienta', primary_key=True)  # The composite primary key (herramienta, edo_herramienta) found, that is not supported. The first column is selected.
    edo_herramienta = models.ForeignKey(EdoHerramienta, models.DO_NOTHING, db_column='edo_herramienta')
    cantidad = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'estado_herramienta'
        unique_together = (('herramienta', 'edo_herramienta'),)

class EstadoRefaccion(models.Model):
    estado_refaccion = models.OneToOneField(EdoRefaccion, models.DO_NOTHING, db_column='estado_refaccion', primary_key=True)  # The composite primary key (estado_refaccion, refaccion) found, that is not supported. The first column is selected.
    refaccion = models.ForeignKey(Refaccion, models.DO_NOTHING, db_column='refaccion')
    cantidad = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'estado_refaccion'
        unique_together = (('estado_refaccion', 'refaccion'),)