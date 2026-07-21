from django.db import models

# Create your models here.
from django.db import models


#    class Maquina(models.Model):
#        codigo = models.CharField(max_length=10, primary_key=True)
#        numeroSerie = models.CharField(max_length=30, unique=True, null=True, blank=True)
#        nombre = models.CharField(max_length=100)
#        descripcion = models.CharField(max_length=255, null=True, blank=True)
#        imagen_url = models.CharField(max_length=255, null=True, blank=True)
#        fechaInstalacion = models.DateField()
#
#        linea = models.CharField(max_length=10, null=True, blank=True)
#        marca = models.CharField(max_length=10, null=True, blank=True)
#        modelo = models.CharField(max_length=10, null=True, blank=True)
#        estado_maquina = models.CharField(max_length=5, null=True, blank=True)
#        tipo_maquina = models.IntegerField(null=True, blank=True)
#
#        class Meta:
#            managed = False
#           db_table = "MAQUINA"
#
#       def __str__(self):
#           return f"{self.codigo} - {self.nombre}"


from django.db import models

# Create your models here.
from django.db import models


# ==========================================================
# CATÁLOGOS
# ==========================================================

class TipoMaquina(models.Model):
    numeroRegistro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "TIPO_MAQUINA"

    def __str__(self):
        return self.nombre


class EstadoMaquina(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "EDO_MAQUINA"

    def __str__(self):
        return self.nombre


class EstadoPieza(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "EDO_PIEZA"

    def __str__(self):
        return self.nombre


class TipoSeveridad(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "TIPO_SEVERIDAD"

    def __str__(self):
        return self.nombre


# ==========================================================
# TRABAJADOR
# ==========================================================

class Trabajador(models.Model):
    numeroNomina = models.CharField(max_length=15, primary_key=True)
    nombre = models.CharField(max_length=50)
    apellidoPat = models.CharField(max_length=50)
    apellidoMat = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=15, unique=True)
    correo = models.EmailField(max_length=100, unique=True)
    usuario = models.CharField(max_length=30, unique=True)
    contraseña = models.CharField(db_column="contraseña", max_length=255)
    actividad = models.BooleanField(default=True)

    rol = models.CharField(max_length=5, blank=True, null=True)
    especialidad = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "TRABAJADOR"

    def __str__(self):
        return f"{self.numeroNomina} - {self.nombre} {self.apellidoPat}"


# ==========================================================
# REFACCIONES
# ==========================================================

class Refaccion(models.Model):
    numeroRegistro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    codigoSku = models.CharField(max_length=30, unique=True)
    puntoReorden = models.IntegerField(blank=True, null=True)
    codigoInventario = models.CharField(max_length=30, unique=True)
    numeroOrden = models.CharField(max_length=20, unique=True)
    costo = models.FloatField()
    tiempoEntregaApr = models.IntegerField(blank=True, null=True)
    stock = models.IntegerField(default=0)
    stockMinimo = models.IntegerField(default=0)

    proveedor = models.CharField(max_length=10, blank=True, null=True)
    tipo_refaccion = models.IntegerField(blank=True, null=True)
    clasificacion = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "REFACCION"

    def __str__(self):
        return self.nombre
    

    # ==========================================================
# MAQUINA
# ==========================================================

class Maquina(models.Model):
    codigo = models.CharField(max_length=10, primary_key=True)
    numeroSerie = models.CharField(max_length=30, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    imagen_url = models.CharField(max_length=255, blank=True, null=True)
    modelo_3d = models.CharField(max_length=255,blank=True,null=True)

    fechaInstalacion = models.DateField()

    linea = models.CharField(max_length=10, blank=True, null=True)
    marca = models.CharField(max_length=10, blank=True, null=True)
    modelo = models.CharField(max_length=10, blank=True, null=True)

    estado_maquina = models.ForeignKey(
        EstadoMaquina,
        on_delete=models.DO_NOTHING,
        db_column="estado_maquina",
        blank=True,
        null=True,
        related_name="maquinas"
    )

    tipo_maquina = models.ForeignKey(
        TipoMaquina,
        on_delete=models.DO_NOTHING,
        db_column="tipo_maquina",
        blank=True,
        null=True,
        related_name="maquinas"
    )

    class Meta:
        managed = False
        db_table = "MAQUINA"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


# ==========================================================
# REFACCIONES COMPATIBLES CON MAQUINA
# ==========================================================

class RefaccMaqui(models.Model):
    numeroRegistro = models.AutoField(primary_key=True)

    maquina = models.ForeignKey(
        Maquina,
        on_delete=models.DO_NOTHING,
        db_column="maquina",
        related_name="refacciones_compatibles"
    )

    refaccion = models.ForeignKey(
        Refaccion,
        on_delete=models.DO_NOTHING,
        db_column="refaccion",
        related_name="maquinas"
    )

    class Meta:
        managed = False
        db_table = "REFACC_MAQUI"

    def __str__(self):
        return f"{self.maquina.codigo} - {self.refaccion.nombre}"
    
# ==========================================================
# PIEZA
# ==========================================================

class Pieza(models.Model):
    numeroSerie = models.CharField(max_length=30, primary_key=True)
    codigoEtiqueta = models.CharField(max_length=30, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=100)

    costoInicial = models.FloatField()
    horasOperacion = models.IntegerField(default=0)
    tiempoVidaUtil = models.IntegerField()

    depresacionAnual = models.FloatField(blank=True, null=True)
    valorResidual = models.FloatField(blank=True, null=True)

    fechaInstalacion = models.DateField()
    fechaGarantia = models.DateField(blank=True, null=True)

    estado_pieza = models.ForeignKey(
        EstadoPieza,
        on_delete=models.DO_NOTHING,
        db_column="edo_pieza",
        blank=True,
        null=True,
        related_name="piezas"
    )

    maquina = models.ForeignKey(
        Maquina,
        on_delete=models.DO_NOTHING,
        db_column="maquina",
        blank=True,
        null=True,
        related_name="piezas"
    )


    tipo_pieza = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "PIEZA"

    def __str__(self):
        return f"{self.nombre} ({self.numeroSerie})"

# ==========================================================
# INDICADOR
# ==========================================================

class Indicador(models.Model):
    numeroRegistro = models.AutoField(primary_key=True)

    fechaInicio = models.DateField(blank=True, null=True)
    fechaFin = models.DateField(blank=True, null=True)

    mttr = models.FloatField(blank=True, null=True)
    mtbf = models.FloatField(blank=True, null=True)
    porcentajeDispo = models.IntegerField(blank=True, null=True)

    maquina = models.ForeignKey(
        Maquina,
        on_delete=models.DO_NOTHING,
        db_column="maquina",
        blank=True,
        null=True,
        related_name="indicadores"
    )

    class Meta:
        managed = False
        db_table = "INDICADOR"

    def __str__(self):
        if self.maquina:
            return f"{self.maquina.codigo} - Indicador {self.numeroRegistro}"
        return f"Indicador {self.numeroRegistro}"
    

# ==========================================================
# REPORTE DE FALLA
# ==========================================================

class ReporteFalla(models.Model):
    numeroRegistro = models.AutoField(primary_key=True)

    asunto = models.CharField(max_length=500)

    fechaResolucion = models.DateField()
    fechaCreacion = models.DateField()
    horaCreacion = models.TimeField()

    tiempoParo = models.IntegerField(blank=True, null=True)

    causaRaiz = models.CharField(max_length=500)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    imagen = models.CharField(max_length=255, blank=True, null=True)

    maquina = models.ForeignKey(
        Maquina,
        on_delete=models.DO_NOTHING,
        db_column="maquina",
        blank=True,
        null=True,
        related_name="reportes_falla"
    )

    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.DO_NOTHING,
        db_column="trabajador",
        blank=True,
        null=True,
        related_name="fallas_atendidas"
    )

    tipo_falla = models.IntegerField(blank=True, null=True)

    tipo_severidad = models.ForeignKey(
        TipoSeveridad,
        on_delete=models.DO_NOTHING,
        db_column="tipo_severidad",
        blank=True,
        null=True,
        related_name="reportes"
    )

    class Meta:
        managed = False
        db_table = "REPORTE_FALLA"

    def __str__(self):
        return f"{self.numeroRegistro} - {self.asunto}"


# ==========================================================
# ORDEN DE MANTENIMIENTO
# ==========================================================

class OrdenMantenimiento(models.Model):
    folio = models.CharField(max_length=15, primary_key=True)

    descripcion = models.CharField(max_length=500)
    diagnostico = models.CharField(max_length=500, blank=True, null=True)
    notas = models.CharField(max_length=500, blank=True, null=True)

    fechaProgramada = models.DateField()
    fechaCreacion = models.DateField()
    horaCreacion = models.TimeField()

    fechaCierre = models.DateField(blank=True, null=True)
    horaCierre = models.TimeField(blank=True, null=True)

    horasIntervenidas = models.FloatField(blank=True, null=True)

    imagen = models.CharField(max_length=255, blank=True, null=True)

    maquina = models.ForeignKey(
        Maquina,
        on_delete=models.DO_NOTHING,
        db_column="maquina",
        blank=True,
        null=True,
        related_name="ordenes_mantenimiento"
    )

    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.DO_NOTHING,
        db_column="trabajador",
        blank=True,
        null=True,
        related_name="ordenes_asignadas"
    )

    reporte_falla = models.ForeignKey(
        ReporteFalla,
        on_delete=models.DO_NOTHING,
        db_column="reporte_falla",
        blank=True,
        null=True,
        related_name="ordenes"
    )

    tipo_mantenimiento = models.CharField(max_length=5, blank=True, null=True)
    estado_orden = models.CharField(max_length=5, blank=True, null=True)

    class Meta:
        managed = False
        db_table = "ORDEN_MANTENIMIENTO"

    def __str__(self):
        return self.folio