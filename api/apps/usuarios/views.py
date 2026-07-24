from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models, serializers


def _verificar_password(trabajador, password):
    """Valida la contraseña acepte esté HASHEADA o en TEXTO PLANO.

    Sirve para poder hacer INSERT manuales con la contraseña tal cual. Si
    estaba en texto plano y coincide, la re-hashea en ese momento para dejarla
    encriptada de aqui en adelante (upgrade on login). Devuelve True/False."""
    stored = trabajador.contrasena or ""

    # ¿El valor guardado tiene formato de hash conocido por Django?
    try:
        identify_hasher(stored)
        es_hash = True
    except ValueError:
        es_hash = False

    if es_hash:
        return check_password(password, stored)

    # Texto plano (p.ej. un INSERT a mano): comparacion directa y, si coincide,
    # se re-hashea para que quede encriptada.
    if password and password == stored:
        trabajador.contrasena = make_password(password)
        trabajador.save(update_fields=["contrasena"])
        return True
    return False


class PingAPIView(APIView):
    """Endpoint de prueba: confirma que el modulo Usuarios responde."""

    def get(self, request):
        return Response({"modulo": "usuarios", "status": "ok"}, status=status.HTTP_200_OK)


class RolListAPIView(generics.ListAPIView):
    """Catalogo de roles, para llenar el <select> del formulario de registro."""

    queryset = models.Rol.objects.all()
    serializer_class = serializers.RolSerializer


class RolCreateAPIView(generics.CreateAPIView):
    queryset = models.Rol.objects.all()
    serializer_class = serializers.RolDetailSerializer


class RolDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Rol.objects.all()
    serializer_class = serializers.RolDetailSerializer
    lookup_field = "codigo"


class EspecialidadListAPIView(generics.ListAPIView):
    """Catalogo de especialidades, para llenar el <select> del formulario de registro."""

    queryset = models.Especialidad.objects.all()
    serializer_class = serializers.EspecialidadSerializer


class EspecialidadCreateAPIView(generics.CreateAPIView):
    queryset = models.Especialidad.objects.all()
    serializer_class = serializers.EspecialidadDetailSerializer


class EspecialidadDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = models.Especialidad.objects.all()
    serializer_class = serializers.EspecialidadDetailSerializer
    lookup_field = "numeroRegistro"


class RegistroAPIView(generics.CreateAPIView):
    """Alta de un TRABAJADOR nuevo. Publico (AllowAny via settings)."""

    serializer_class = serializers.RegistroTrabajadorSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        trabajador = serializer.save()
        data = serializers.TrabajadorSerializer(trabajador, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)


# ------------ TRABAJADOR ------------
class TrabajadorListAPIView(generics.ListAPIView):
    queryset = models.Trabajador.objects.select_related("rol", "especialidad").order_by("nombre")
    serializer_class = serializers.TrabajadorSerializer  # ya excluye password, no cambiar


class TrabajadorDetailAPIView(generics.RetrieveUpdateAPIView):
    # SIN Destroy a propósito: un trabajador no se borra físico (rompería
    # FKs de ordenes/reportes ya asignados), se da de baja con el campo
    # 'actividad' via PATCH. No agregues DELETE aquí.
    queryset = models.Trabajador.objects.select_related("rol", "especialidad")
    lookup_field = "numeroNomina"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.UpdateTrabajadorSerializer
        return serializers.TrabajadorSerializer


class LoginAPIView(APIView):
    """Login con correo O usuario + contraseña contra la tabla TRABAJADOR.
    No usa el sistema de auth/token de Django: compara el hash a mano con
    check_password. Regresa los datos del trabajador si es correcto."""

    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identificador = serializer.validated_data["identificador"].strip()
        password = serializer.validated_data["password"]

        trabajador = models.Trabajador.objects.filter(
            Q(correo__iexact=identificador) | Q(usuario__iexact=identificador)
        ).first()

        if trabajador is None or not _verificar_password(trabajador, password):
            return Response(
                {"detail": "Usuario/correo o contraseña incorrectos."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not trabajador.actividad:
            return Response(
                {"detail": "Este usuario está dado de baja. Contacta a un administrador."},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = serializers.TrabajadorSerializer(trabajador, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)