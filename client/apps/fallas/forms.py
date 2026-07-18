from django import forms
from apps.fallas.models import EdoReporte, TipoFalla, ReporteFalla, TipoSeveridad
from api.apps.maquinaria.models import Maquina
from api.apps.usuarios.models import Trabajador

class CrearTipoFalla(forms.Form):
    nombre = forms.CharField(max_length=50, required=True)
    descripcion = forms.CharField(max_length=255, required=False)

class CrearTipoSeveridad(forms.Form):
    codigo = forms.CharField(max_length=5, required=True)
    nombre = forms.CharField(max_length=30, required=True)
    descripcion = forms.CharField(max_length=255, required=False)

class CrearEdoReporte(forms.Form):
    codigo = forms.CharField(max_length=5, required=True)
    nombre = forms.CharField(max_length=50, required=True)
    descripcion = forms.CharField(max_length=255, required=False)

class CrearTipoReporte(forms.Form):
    tipo_falla = forms.ModelChoiceField(queryset=TipoFalla.objects.all(), required=True)
    reporte_falla = forms.ModelChoiceField(queryset=ReporteFalla.objects.all(), required=True)

class CrearReporteFalla(forms.Form):
    asunto = forms.CharField(max_length=500, required=True)
    fecharesolucion = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    fechacreacion = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    horacreacion = forms.TimeField(required=True, widget=forms.TimeInput(attrs={'type': 'time'}))
    tiempoparo = forms.IntegerField(required=False)
    causaraiz = forms.CharField(max_length=500, required=True)
    descripcion = forms.CharField(max_length=500, required=False)
    imagen = forms.CharField(max_length=255, required=False)
    maquina = forms.ModelChoiceField(queryset=Maquina.objects.all(), required=False)
    trabajador = forms.ModelChoiceField(queryset=Trabajador.objects.all(), required=False)
    tipo_falla = forms.ModelChoiceField(queryset=TipoFalla.objects.all(), required=False)
    tipo_severidad = forms.ModelChoiceField(queryset=TipoSeveridad.objects.all(), required=False)