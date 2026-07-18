from django.db import models


class Area(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(unique=True, max_length=15)
    planta = models.ForeignKey('Planta', models.DO_NOTHING, db_column='planta')

    class Meta:
        managed = False
        db_table = 'area'


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


class EdoMaquina(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_maquina'


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


class EdoReporte(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'edo_reporte'


class Especialidad(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'especialidad'


class EstadoHerramienta(models.Model):
    herramienta = models.OneToOneField('Herramienta', models.DO_NOTHING, db_column='herramienta', primary_key=True)  # The composite primary key (herramienta, edo_herramienta) found, that is not supported. The first column is selected.
    edo_herramienta = models.ForeignKey(EdoHerramienta, models.DO_NOTHING, db_column='edo_herramienta')
    cantidad = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'estado_herramienta'
        unique_together = (('herramienta', 'edo_herramienta'),)


class EstadoOrden(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'estado_orden'


class EstadoRefaccion(models.Model):
    estado_refaccion = models.OneToOneField(EdoRefaccion, models.DO_NOTHING, db_column='estado_refaccion', primary_key=True)  # The composite primary key (estado_refaccion, refaccion) found, that is not supported. The first column is selected.
    refaccion = models.ForeignKey('Refaccion', models.DO_NOTHING, db_column='refaccion')
    cantidad = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'estado_refaccion'
        unique_together = (('estado_refaccion', 'refaccion'),)


class HerraOrden(models.Model):
    herramienta = models.OneToOneField('Herramienta', models.DO_NOTHING, db_column='herramienta', primary_key=True)  # The composite primary key (herramienta, orden_mantenimiento) found, that is not supported. The first column is selected.
    orden_mantenimiento = models.ForeignKey('OrdenMantenimiento', models.DO_NOTHING, db_column='orden_mantenimiento')

    class Meta:
        managed = False
        db_table = 'herra_orden'
        unique_together = (('herramienta', 'orden_mantenimiento'),)


class Herramienta(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    tipo_herramienta = models.ForeignKey('TipoHerramienta', models.DO_NOTHING, db_column='tipo_herramienta', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'herramienta'


class Indicador(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    fechainicio = models.DateField(db_column='fechaInicio', blank=True, null=True)  # Field name made lowercase.
    fechafin = models.DateField(db_column='fechaFin', blank=True, null=True)  # Field name made lowercase.
    mttr = models.FloatField(blank=True, null=True)
    mtbf = models.FloatField(blank=True, null=True)
    porcentajedispo = models.IntegerField(db_column='porcentajeDispo', blank=True, null=True)  # Field name made lowercase.
    maquina = models.ForeignKey('Maquina', models.DO_NOTHING, db_column='maquina', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'indicador'


class Linea(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    area = models.ForeignKey(Area, models.DO_NOTHING, db_column='area')

    class Meta:
        managed = False
        db_table = 'linea'


class Maquina(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    numeroserie = models.CharField(db_column='numeroSerie', unique=True, max_length=30, blank=True, null=True)  # Field name made lowercase.
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    imagen_url = models.CharField(max_length=255, blank=True, null=True)
    fechainstalacion = models.DateField(db_column='fechaInstalacion')  # Field name made lowercase.
    linea = models.ForeignKey(Linea, models.DO_NOTHING, db_column='linea', blank=True, null=True)
    marca = models.ForeignKey('Marca', models.DO_NOTHING, db_column='marca', blank=True, null=True)
    modelo = models.ForeignKey('Modelo', models.DO_NOTHING, db_column='modelo', blank=True, null=True)
    estado_maquina = models.ForeignKey(EdoMaquina, models.DO_NOTHING, db_column='estado_maquina', blank=True, null=True)
    tipo_maquina = models.ForeignKey('TipoMaquina', models.DO_NOTHING, db_column='tipo_maquina', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maquina'


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


class Movimiento(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    tipomovimiento = models.CharField(db_column='tipoMovimiento', max_length=20)  # Field name made lowercase.
    orden_mantenimiento = models.ForeignKey('OrdenMantenimiento', models.DO_NOTHING, db_column='orden_mantenimiento', blank=True, null=True)
    refaccion = models.ForeignKey('Refaccion', models.DO_NOTHING, db_column='refaccion', blank=True, null=True)
    pieza = models.ForeignKey('Refaccion', models.DO_NOTHING, db_column='PIEZA', related_name='movimiento_pieza_set', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'movimiento'


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
    trabajador = models.ForeignKey('Trabajador', models.DO_NOTHING, db_column='trabajador', blank=True, null=True)
    reporte_falla = models.ForeignKey('ReporteFalla', models.DO_NOTHING, db_column='reporte_falla', blank=True, null=True)
    tipo_mantenimiento = models.ForeignKey('TipoMantenimiento', models.DO_NOTHING, db_column='tipo_mantenimiento', blank=True, null=True)
    estado_orden = models.ForeignKey(EstadoOrden, models.DO_NOTHING, db_column='estado_orden', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orden_mantenimiento'


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
    tipo_pieza = models.ForeignKey('TipoPieza', models.DO_NOTHING, db_column='tipo_pieza', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'pieza'


class Planta(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    nombre = models.CharField(unique=True, max_length=100)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(unique=True, max_length=15)
    dircalle = models.CharField(db_column='dirCalle', max_length=100)  # Field name made lowercase.
    dircodigopostal = models.CharField(db_column='dirCodigoPostal', max_length=5)  # Field name made lowercase.
    dirnumero = models.CharField(db_column='dirNumero', max_length=10)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'planta'


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


class RefaccMaqui(models.Model):
    maquina = models.OneToOneField(Maquina, models.DO_NOTHING, db_column='maquina', primary_key=True)  # The composite primary key (maquina, refaccion) found, that is not supported. The first column is selected.
    refaccion = models.ForeignKey('Refaccion', models.DO_NOTHING, db_column='refaccion')

    class Meta:
        managed = False
        db_table = 'refacc_maqui'
        unique_together = (('maquina', 'refaccion'),)


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
    tipo_refaccion = models.ForeignKey('TipoRefaccion', models.DO_NOTHING, db_column='tipo_refaccion', blank=True, null=True)
    clasificacion = models.ForeignKey(Clasificacion, models.DO_NOTHING, db_column='clasificacion', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'refaccion'


class RegistroOps(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    fechainicio = models.DateField(db_column='fechaInicio')  # Field name made lowercase.
    fechafin = models.DateField(db_column='fechaFin')  # Field name made lowercase.
    horasoperacion = models.IntegerField(db_column='horasOperacion')  # Field name made lowercase.
    maquina = models.ForeignKey(Maquina, models.DO_NOTHING, db_column='maquina')

    class Meta:
        managed = False
        db_table = 'registro_ops'


class ReporteFalla(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    asunto = models.CharField(max_length=500)
    fecharesolucion = models.DateField(db_column='fechaResolucion')  # Field name made lowercase.
    fechacreacion = models.DateField(db_column='fechaCreacion')  # Field name made lowercase.
    horacreacion = models.TimeField(db_column='horaCreacion')  # Field name made lowercase.
    tiempoparo = models.IntegerField(db_column='tiempoParo', blank=True, null=True)  # Field name made lowercase.
    causaraiz = models.CharField(db_column='causaRaiz', max_length=500)  # Field name made lowercase.
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    maquina = models.ForeignKey(Maquina, models.DO_NOTHING, db_column='maquina', blank=True, null=True)
    trabajador = models.ForeignKey('Trabajador', models.DO_NOTHING, db_column='trabajador', blank=True, null=True)
    tipo_falla = models.ForeignKey('TipoFalla', models.DO_NOTHING, db_column='tipo_falla', blank=True, null=True)
    tipo_severidad = models.ForeignKey('TipoSeveridad', models.DO_NOTHING, db_column='tipo_severidad', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'reporte_falla'


class Rol(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'rol'


class TareaOrden(models.Model):
    tarea = models.OneToOneField('Tareas', models.DO_NOTHING, db_column='tarea', primary_key=True)  # The composite primary key (tarea, orden_mantenimiento) found, that is not supported. The first column is selected.
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


class Tareas(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    instruccion = models.CharField(max_length=100)
    actividad = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'tareas'


class TipoFalla(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_falla'


class TipoHerramienta(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_herramienta'


class TipoMantenimiento(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_mantenimiento'


class TipoMaquina(models.Model):
    numeroregistro = models.AutoField(db_column='numeroRegistro', primary_key=True)  # Field name made lowercase.
    nombre = models.CharField(unique=True, max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_maquina'


class TipoMovimiento(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_movimiento'


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

class TipoReporte(models.Model):
    tipo_falla = models.OneToOneField(TipoFalla, models.DO_NOTHING, db_column='tipo_falla', primary_key=True)  # The composite primary key (tipo_falla, reporte_falla) found, that is not supported. The first column is selected.
    reporte_falla = models.ForeignKey(ReporteFalla, models.DO_NOTHING, db_column='reporte_falla')

    class Meta:
        managed = False
        db_table = 'tipo_reporte'
        unique_together = (('tipo_falla', 'reporte_falla'),)


class TipoSeveridad(models.Model):
    codigo = models.CharField(primary_key=True, max_length=5)
    nombre = models.CharField(unique=True, max_length=30)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tipo_severidad'


class TrabaOrdePersonal(models.Model):
    trabajador = models.OneToOneField('Trabajador', models.DO_NOTHING, db_column='trabajador', primary_key=True)  # The composite primary key (trabajador, orden_mantenimiento) found, that is not supported. The first column is selected.
    orden_mantenimiento = models.ForeignKey(OrdenMantenimiento, models.DO_NOTHING, db_column='orden_mantenimiento')

    class Meta:
        managed = False
        db_table = 'traba_orde_personal'
        unique_together = (('trabajador', 'orden_mantenimiento'),)


class Trabajador(models.Model):
    numeronomina = models.CharField(db_column='numeroNomina', primary_key=True, max_length=15)  # Field name made lowercase.
    nombre = models.CharField(max_length=50)
    apellidopat = models.CharField(db_column='apellidoPat', max_length=50)  # Field name made lowercase.
    apellidomat = models.CharField(db_column='apellidoMat', max_length=50, blank=True, null=True)  # Field name made lowercase.
    telefono = models.CharField(unique=True, max_length=15)
    correo = models.CharField(unique=True, max_length=100)
    usuario = models.CharField(unique=True, max_length=30)
    contraseña = models.CharField(max_length=255)
    actividad = models.IntegerField()
    rol = models.ForeignKey(Rol, models.DO_NOTHING, db_column='rol', blank=True, null=True)
    especialidad = models.ForeignKey(Especialidad, models.DO_NOTHING, db_column='especialidad', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trabajador'
