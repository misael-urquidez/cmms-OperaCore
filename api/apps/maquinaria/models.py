from django.db import models

# ==========================================================
# CATÁLOGOS Y UBICACIONES
# ==========================================================

class Planta(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(unique=True, max_length=15)
    dircalle = models.CharField(db_column='dirCalle', max_length=100)
    dircodigopostal = models.CharField(db_column='dirCodigoPostal', max_length=5)
    dirnumero = models.CharField(db_column='dirNumero', max_length=10)

    class Meta:
        managed = False
        db_table = 'planta'

class Area(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(unique=True, max_length=15)
    planta = models.ForeignKey(Planta, models.DO_NOTHING, db_column='planta')

    class Meta:
        managed = False
        db_table = 'area'

class EdoMaquina(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_maquina'

    def __str__(self):
        return self.nombre

class Linea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    area = models.ForeignKey(Area, models.DO_NOTHING, db_column='area')

    class Meta:
        managed = False
        db_table = 'linea'
    
class Marca(models.Model):
    clave = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'marca'

class Modelo(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    marca = models.ForeignKey(Marca, models.DO_NOTHING, db_column='marca')

    class Meta:
        managed = False
        db_table = 'modelo'

class TipoMaquina(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_maquina'

    def __str__(self):
        return self.nombre

# ==========================================================
# MAQUINA
# ==========================================================

class Maquina(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    numeroserie = models.CharField(db_column='numeroSerie', unique=True, max_length=30, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    imagen_url = models.CharField(max_length=255, blank=True, null=True)
    modelo_3d = models.CharField(max_length=255, blank=True, null=True)
    fechainstalacion = models.DateField(db_column='fechaInstalacion')
    
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)
    marca = models.ForeignKey(Marca, models.DO_NOTHING, db_column='marca', blank=True, null=True)
    modelo = models.ForeignKey(Modelo, models.DO_NOTHING, db_column='modelo', blank=True, null=True)
    estado_maquina = models.ForeignKey(EdoMaquina, models.DO_NOTHING, db_column='estado_maquina', blank=True, null=True)
    tipo_maquina = models.ForeignKey(TipoMaquina, models.DO_NOTHING, db_column='tipo_maquina', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maquina'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"