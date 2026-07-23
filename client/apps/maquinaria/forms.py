from django import forms

ESTADO_CHOICES = [
    ("Operativa", "Operativa"),
    ("En Mantenimiento", "En Mantenimiento"),
    ("En Falla", "En Falla"),
    ("Inactiva", "Inactiva"),
]

TIPO_CHOICES = [
    ("Pick & Place", "Pick & Place"),
    ("Horno Reflow", "Horno Reflow"),
    ("AOI", "AOI"),
    ("Dispensador de pasta", "Dispensador de pasta"),
    ("Transportador", "Transportador"),
    ("Estación de prueba", "Estación de prueba"),
]

LINEA_CHOICES = [
    ("LI001", "Línea 1 (SMT Principal)"),
    ("LI002", "Línea 2 (Secundaria)"),
]

class MaquinaForm(forms.Form):
    numeroSerie = forms.CharField(
        max_length=100, 
        label="Número de Serie"
    )
    nombre = forms.CharField(
        max_length=150, 
        label="Nombre del Equipo"
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}), 
        required=False, 
        label="Descripción"
    )
    
    imagen_url = forms.ImageField(
        required=False, 
        label="Fotografía del Equipo",
        widget=forms.ClearableFileInput(attrs={
            "style": "position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none;"
        })
    )
    modelo_3d = forms.FileField(
        required=False, 
        label="Archivo Modelo 3D (.glb)",
        widget=forms.ClearableFileInput(attrs={
            "style": "position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none;"
        })
    )
    
    fechaInstalacion = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "style": "color-scheme: dark;"  # Esto hace que el calendario desplegable del navegador combine con el tema oscuro
        }), 
        label="Fecha de Instalación"
    )
    
    linea = forms.ChoiceField(
        choices=LINEA_CHOICES, 
        label="Línea de Producción"
    )
    
    marca = forms.CharField(
        max_length=100, 
        label="Marca del Fabricante"
    )
    modelo = forms.CharField(
        max_length=100, 
        label="Modelo"
    )
    
    estado_maquina = forms.ChoiceField(
        choices=ESTADO_CHOICES, 
        initial="Operativa", 
        label="Estado Operativo"
    )
    tipo_maquina = forms.ChoiceField(
        choices=TIPO_CHOICES, 
        label="Tipo de Máquina"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name not in ['imagen_url', 'modelo_3d']:
                existing_classes = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing_classes}".strip()