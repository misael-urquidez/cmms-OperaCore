from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import *


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ["codigo", "nombre"]


class RolDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ["codigo", "nombre", "descripcion"]


class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ["codigo", "nombre"]


class EspecialidadDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ["codigo", "nombre", "descripcion"]


class TrabajadorSerializer(serializers.ModelSerializer):
    """Representación pública (SIN contraseña). Se usa en las respuestas de
    login y registro."""

    rol_nombre = serializers.CharField(source="rol.nombre", read_only=True, default=None)
    especialidad_nombre = serializers.CharField(source="especialidad.nombre", read_only=True, default=None)

    class Meta:
        model = Trabajador
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
        model = Trabajador
        fields = [
            "nombre", "apellidoPat", "apellidoMat", "telefono",
            "correo", "usuario", "password", "password2", "rol", "especialidad",
        ]

    def validate_usuario(self, value):
        if Trabajador.objects.filter(usuario__iexact=value).exists():
            raise serializers.ValidationError("Ese usuario ya existe.")
        return value

    def validate_correo(self, value):
        if Trabajador.objects.filter(correo__iexact=value).exists():
            raise serializers.ValidationError("Ese correo ya está registrado.")
        return value

    def validate_telefono(self, value):
        if Trabajador.objects.filter(telefono=value).exists():
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

        for _ in range(5):
            trabajador = Trabajador(
                numeroNomina=generar_numero_nomina(),
                contrasena=hashed,
                **validated_data,
            )
            try:
                with transaction.atomic():
                    trabajador.save(force_insert=True)
                return trabajador
            except IntegrityError as exc:
                if "PRIMARY" not in str(exc):
                    raise

        raise serializers.ValidationError(
            {"detail": "No se pudo asignar un número de nómina disponible. Intenta de nuevo."}
        )


class UpdateTrabajadorSerializer(serializers.ModelSerializer):
    """Edición de un TRABAJADOR existente. password es opcional."""

    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Trabajador
        fields = [
            "nombre", "apellidoPat", "apellidoMat", "telefono", "correo",
            "usuario", "actividad", "rol", "especialidad", "password",
        ]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.contrasena = make_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """identificador = correo o usuario, indistintamente."""

    identificador = serializers.CharField()
    password = serializers.CharField(write_only=True)