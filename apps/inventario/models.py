from django.db import models

# =====================================================================
# NOTA IMPORTANTE (leer antes de correr migrate):
#
# Todavía no está decidido con el equipo si:
#   (a) Django crea las tablas con `migrate` (managed = True), o
#   (b) los modelos apuntan a las tablas que ya existen en beta.sql
#       (managed = False).
#
# Estos modelos funcionan en AMBOS casos porque cada `db_table` y
# `db_column` ya está mapeado exactamente a los nombres de beta.sql.
# Cuando el equipo decida, solo cambien `managed` en cada Meta
# (o bórrenlo, porque managed = True es el default de Django).
#
# Por ahora lo dejamos en managed = True (opción recomendada mientras
# no exista una decisión formal, ya que maquinaria tampoco la tiene).
# =====================================================================

MANAGED = True


# ---------------------------------------------------------------------
# Catálogos (tablas que ya existen en otras apps del esquema, pero que
# inventario necesita referenciar). Si maquinaria/otra app ya los
# define en su propio models.py, borren estas clases de aquí y
# importen las suyas para no duplicar la tabla.
# ---------------------------------------------------------------------

class TipoRefaccion(models.Model):
    numero_registro = models.AutoField(db_column='numeroRegistro', primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'TIPO_REFACCION'
        managed = MANAGED

    def __str__(self):
        return self.nombre


class Clasificacion(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'CLASIFICACION'
        managed = MANAGED

    def __str__(self):
        return self.nombre


class EdoRefaccion(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'EDO_REFACCION'
        managed = MANAGED

    def __str__(self):
        return self.nombre


class TipoHerramienta(models.Model):
    numero_registro = models.AutoField(db_column='numeroRegistro', primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'TIPO_HERRAMIENTA'
        managed = MANAGED

    def __str__(self):
        return self.nombre


class EdoHerramienta(models.Model):
    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'EDO_HERRAMIENTA'
        managed = MANAGED

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    codigo = models.CharField(max_length=10, primary_key=True)
    rfc = models.CharField(max_length=13, unique=True)
    razon_social = models.CharField(db_column='razonSocial', max_length=100, unique=True)
    nombre_comercial = models.CharField(db_column='nombreComercial', max_length=100, unique=True)
    telefono = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    dir_calle = models.CharField(db_column='dirCalle', max_length=100)
    dir_codigo_postal = models.CharField(db_column='dirCodigoPostal', max_length=5)
    dir_numero = models.CharField(db_column='dirNumero', max_length=10)
    cont_nombre = models.CharField(db_column='contNombre', max_length=50)
    cont_apell_pat = models.CharField(db_column='contApellPat', max_length=50)
    cont_apell_mat = models.CharField(db_column='contApellMat', max_length=50, null=True, blank=True)

    class Meta:
        db_table = 'PROVEEDOR'
        managed = MANAGED

    def __str__(self):
        return self.nombre_comercial


# ---------------------------------------------------------------------
# Núcleo del módulo de inventario
# ---------------------------------------------------------------------

class Refaccion(models.Model):
    numero_registro = models.AutoField(db_column='numeroRegistro', primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    codigo_sku = models.CharField(db_column='codigoSku', max_length=30, unique=True)
    punto_reorden = models.IntegerField(db_column='puntoReorden', null=True, blank=True)
    codigo_inventario = models.CharField(db_column='codigoInventario', max_length=30, unique=True)
    numero_orden = models.CharField(db_column='numeroOrden', max_length=20, unique=True)
    costo = models.FloatField()
    tiempo_entrega_apr = models.IntegerField(db_column='tiempoEntregaApr', null=True, blank=True)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(db_column='stockMinimo', default=0)
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='proveedor', related_name='refacciones',
    )
    tipo_refaccion = models.ForeignKey(
        TipoRefaccion, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='tipo_refaccion', related_name='refacciones',
    )
    clasificacion = models.ForeignKey(
        Clasificacion, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='clasificacion', related_name='refacciones',
    )

    class Meta:
        db_table = 'REFACCION'
        managed = MANAGED

    def __str__(self):
        return f'{self.nombre} ({self.codigo_sku})'

    @property
    def stock_bajo(self):
        """
        True si el stock está en o por debajo del mínimo, o si ya llegó
        al punto de reorden. Esto es lo que alimenta la alerta visual
        que pide el objetivo 4 del proyecto.
        """
        if self.stock <= self.stock_minimo:
            return True
        if self.punto_reorden is not None and self.stock <= self.punto_reorden:
            return True
        return False


class Herramienta(models.Model):
    numero_registro = models.AutoField(db_column='numeroRegistro', primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    imagen = models.CharField(max_length=255, null=True, blank=True)
    tipo_herramienta = models.ForeignKey(
        TipoHerramienta, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='tipo_herramienta', related_name='herramientas',
    )

    class Meta:
        db_table = 'HERRAMIENTA'
        managed = MANAGED

    def __str__(self):
        return self.nombre


class EstadoRefaccion(models.Model):
    """Cuántas unidades de una refacción están disponibles / dañadas / en uso, etc."""
    estado_refaccion = models.ForeignKey(
        EdoRefaccion, on_delete=models.CASCADE, db_column='estado_refaccion',
    )
    refaccion = models.ForeignKey(
        Refaccion, on_delete=models.CASCADE, db_column='refaccion',
        related_name='estados',
    )
    cantidad = models.IntegerField(default=0)

    class Meta:
        db_table = 'ESTADO_REFACCION'
        managed = MANAGED
        unique_together = (('estado_refaccion', 'refaccion'),)

    def __str__(self):
        return f'{self.refaccion} - {self.estado_refaccion}: {self.cantidad}'


class EstadoHerramienta(models.Model):
    herramienta = models.ForeignKey(
        Herramienta, on_delete=models.CASCADE, db_column='herramienta',
        related_name='estados',
    )
    edo_herramienta = models.ForeignKey(
        EdoHerramienta, on_delete=models.CASCADE, db_column='edo_herramienta',
    )
    cantidad = models.IntegerField(default=0)

    class Meta:
        db_table = 'ESTADO_HERRAMIENTA'
        managed = MANAGED
        unique_together = (('herramienta', 'edo_herramienta'),)

    def __str__(self):
        return f'{self.herramienta} - {self.edo_herramienta}: {self.cantidad}'


class Movimiento(models.Model):
    ENTRADA = 'ENTRADA'
    SALIDA = 'SALIDA'
    TIPO_CHOICES = [
        (ENTRADA, 'Entrada'),
        (SALIDA, 'Salida'),
    ]

    numero_registro = models.AutoField(db_column='numeroRegistro', primary_key=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    fecha = models.DateField()
    hora = models.TimeField()
    tipo_movimiento = models.CharField(
        db_column='tipoMovimiento', max_length=20, choices=TIPO_CHOICES,
    )
    # OJO: la app "mantenimiento" todavía no existe / no tiene modelos.
    # Cuando la definan, confirmen que la clase se llama "OrdenMantenimiento"
    # y que su PK es "folio" (así está en beta.sql). Si el nombre real es
    # otro, solo hay que cambiar el string de abajo.
    orden_mantenimiento = models.ForeignKey(
        'mantenimiento.OrdenMantenimiento',
        on_delete=models.SET_NULL, null=True, blank=True,
        db_column='orden_mantenimiento', to_field='folio',
        related_name='movimientos',
    )
    refaccion = models.ForeignKey(
        Refaccion, on_delete=models.SET_NULL, null=True, blank=True,
        db_column='refaccion', related_name='movimientos',
    )
    # NOTA: beta.sql también tiene una columna "PIEZA" en MOVIMIENTO, pero
    # su FK apunta otra vez a REFACCION (probablemente un error de copiado
    # en el .sql, porque sí existe una tabla PIEZA separada). La dejamos
    # fuera del modelo a propósito -- coméntenlo con el equipo antes de
    # agregarla, para no duplicar la relación con refaccion.

    class Meta:
        db_table = 'MOVIMIENTO'
        managed = MANAGED

    def __str__(self):
        return f'{self.tipo_movimiento} #{self.numero_registro} - {self.refaccion}'