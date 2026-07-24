import re

from django.db import models


class Rol(models.Model):
    """Mapea la tabla ROL, ya creada por el script SQL (managed=False:
    Django NO va a crear/alterar esta tabla, solo la lee/escribe)."""

    codigo = models.CharField(max_length=5, primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ROL"

    def __str__(self):
        return self.nombre


class Especialidad(models.Model):
    """Mapea la tabla ESPECIALIDAD (managed=False)."""

    numeroRegistro = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        managed = False
        db_table = "ESPECIALIDAD"

    def __str__(self):
        return self.nombre


class Trabajador(models.Model):
    """Mapea la tabla TRABAJADOR (managed=False). Es el usuario real del
    sistema: se usa tanto para registrarse como para iniciar sesion."""

    numeroNomina = models.CharField(max_length=15, primary_key=True, db_column="numeroNomina")
    nombre = models.CharField(max_length=50)
    apellidoPat = models.CharField(max_length=50, db_column="apellidoPat")
    apellidoMat = models.CharField(max_length=50, null=True, blank=True, db_column="apellidoMat")
    telefono = models.CharField(max_length=15, unique=True)
    correo = models.CharField(max_length=100, unique=True)
    usuario = models.CharField(max_length=30, unique=True)
    foto = models.ImageField(upload_to="trabajadores/", max_length=255, null=True, blank=True)
    # Ojo: en la BD la columna se llama "contraseña" (con ñ). El atributo en
    # Python es "contrasena" para no batallar con el encoding en el codigo.
    contrasena = models.CharField(max_length=255, db_column="contraseña")
    actividad = models.BooleanField(default=True)
    rol = models.ForeignKey(
        Rol, on_delete=models.DO_NOTHING, db_column="rol", null=True, blank=True
    )
    especialidad = models.ForeignKey(
        Especialidad, on_delete=models.DO_NOTHING, db_column="especialidad", null=True, blank=True
    )

    class Meta:
        managed = False
        db_table = "TRABAJADOR"

    def __str__(self):
        return f"{self.numeroNomina} - {self.nombre} {self.apellidoPat}"


def generar_numero_nomina():
    """numeroNomina no es autoincremental (es VARCHAR), asi que generamos
    uno tipo EMP0001, EMP0002... buscando el ultimo registrado."""
    ultimo = (
        Trabajador.objects.filter(numeroNomina__startswith="EMP")
        .order_by("-numeroNomina")
        .values_list("numeroNomina", flat=True)
        .first()
    )
    siguiente = 1
    if ultimo:
        match = re.search(r"(\d+)$", ultimo)
        if match:
            siguiente = int(match.group(1)) + 1
    return f"EMP{siguiente:04d}"