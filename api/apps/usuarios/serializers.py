from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers

from . import models


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Rol
        fields = ["codigo", "nombre"]


class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Especialidad
        fields = ["codigo", "nombre"]


class TrabajadorSerializer(serializers.ModelSerializer):
    """Representación pública (SIN contraseña). Se usa en las respuestas de
    login y registro."""

    rol_nombre = serializers.CharField(source="rol.nombre", read_only=True, default=None)
    especialidad_nombre = serializers.CharField(source="especialidad.nombre", read_only=True, default=None)

    class Meta:
        model = models.Trabajador
        fields = [
            "numeroNomina", "nombre", "apellidoPat", "apellidoMat",
            "telefono", "correo", "usuario", "actividad",
            "rol", "rol_nombre", "especialidad", "especialidad_nombre",
        ]


class RegistroTrabajadorSerializer(serializers.ModelSerializer):
    """Alta de un TRABAJADOR nuevo. numeroNomina se genera solo, la
    contraseña se guarda hasheada con el hasher de Django."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, label="Confirmar contraseña")

    class Meta:
        model = models.Trabajador
        fields = [
            "nombre", "apellidoPat", "apellidoMat", "telefono",
            "correo", "usuario", "password", "password2", "rol", "especialidad",
        ]

    def validate_usuario(self, value):
        if models.Trabajador.objects.filter(usuario__iexact=value).exists():
            raise serializers.ValidationError("Ese usuario ya existe.")
        return value

    def validate_correo(self, value):
        if models.Trabajador.objects.filter(correo__iexact=value).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return value

    def validate_telefono(self, value):
        if models.Trabajador.objects.filter(telefono=value).exists():
            raise serializers.ValidationError("Ese teléfono ya está registrado.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        hashed = make_password(password)

        # numeroNomina NO es autoincremental: lo calculamos nosotros (EMPxxxx).
        # Si dos altas ocurren casi al mismo tiempo (o por un doble envio),
        # ambas pueden calcular el mismo numero y chocar en la llave primaria.
        # Reintentamos con el siguiente numero ante ese choque puntual.
        for _ in range(5):
            trabajador = models.Trabajador(
                numeroNomina=models.generar_numero_nomina(),
                contrasena=hashed,
                **validated_data,
            )
            try:
                with transaction.atomic():
                    trabajador.save(force_insert=True)
                return trabajador
            except IntegrityError as exc:
                # Solo reintentamos si el choque fue por la PRIMARY (numeroNomina).
                # Duplicados de correo/usuario/telefono se propagan para que se
                # reporten como error de validacion normal.
                if "PRIMARY" not in str(exc):
                    raise

        raise serializers.ValidationError(
            {"detail": "No se pudo asignar un número de nómina disponible. Intenta de nuevo."}
        )


class LoginSerializer(serializers.Serializer):
    """identificador = correo o usuario, indistintamente."""

    identificador = serializers.CharField()
    password = serializers.CharField(write_only=True)