import requests
from django import forms
from django.conf import settings
from django.core.cache import cache

API_URL = f"{settings.API_BASE_URL}/maquinaria"
SESSION = requests.Session()

# Mismo TTL que usa maquinaria/views.py para estos catálogos, así comparten
# la misma entrada de caché y no se duplican llamadas al API.
CATALOGO_TTL = 300


class ModeloSelect(forms.Select):
    """<select> de Modelo que además marca cada <option> con la marca a la
    que pertenece (data-marca="..."). El JS del template usa ese atributo
    para mostrar solo los modelos de la marca elegida (cascada marca -> modelo),
    sin tener que volver a pegarle al API cada vez que cambias la marca."""

    def __init__(self, *args, modelo_a_marca=None, **kwargs):
        self.modelo_a_marca = modelo_a_marca or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if value:
            option["attrs"]["data-marca"] = self.modelo_a_marca.get(str(value), "")
        return option


def _fetch_catalogo(endpoint, cache_key):
    """GET a un catálogo del API con caché corta. Nunca truena: si el API
    no responde, regresa lista vacía y el <select> sale sin opciones (mejor
    a que la página completa reviente)."""
    data = cache.get(cache_key)
    if data is not None:
        return data
    try:
        res = SESSION.get(f"{API_URL}/{endpoint}", timeout=5)
        data = res.json() if res.status_code == 200 else []
    except requests.exceptions.RequestException:
        data = []
    cache.set(cache_key, data, CATALOGO_TTL)
    return data


class MaquinaForm(forms.Form):
    """Alta de máquina.

    IMPORTANTE: los nombres de los campos de este form coinciden EXACTO con
    los que espera `CreateMaquinaSerializer` en el API (apps/maquinaria/
    serializers.py del proyecto cmms). No renombrar sin revisar ese archivo,
    porque el API es case-sensitive y un nombre distinto simplemente hace
    que el campo llegue vacío/ignorado.
    """

    codigo = forms.CharField(
        max_length=10,
        required=False,
        label="Código",
        help_text="Déjalo vacío para autogenerarlo (MAQ001, MAQ002, ...).",
        widget=forms.TextInput(attrs={"placeholder": "MAQ001"}),
    )
    numeroserie = forms.CharField(
        max_length=30,
        required=False,
        label="Número de Serie",
        widget=forms.TextInput(attrs={"placeholder": "SN-2024-001"}),
    )
    nombre = forms.CharField(
        max_length=100,
        label="Nombre del Equipo",
        widget=forms.TextInput(attrs={"placeholder": "Pick & Place 2"}),
    )
    descripcion = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Descripción breve del equipo..."}),
        required=False,
        label="Descripción",
    )

    # Los names 'imagen_url' y 'modelo_3d' se mantienen así porque el
    # template (crear_maquina.html) y su JS (maquina3d.js) ya usan esos ids
    # (#id_imagen_url, #id_modelo_3d) para la vista previa / visor 3D.
    # El mapeo al nombre real que espera el API se hace en views.py.
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

    fechainstalacion = forms.DateField(
        widget=forms.DateInput(attrs={
            "type": "date",
            "style": "color-scheme: dark;",
        }),
        label="Fecha de Instalación",
    )

    # Los choices de estos 4 campos se llenan en __init__ jalando los
    # catálogos reales del API (igual que hace apps/gestion/views.py con
    # _fetch_fk_choices). Así nunca se desincronizan de lo que hay en BD.
    # Nota: no existe campo estado_maquina: toda máquina nueva se crea
    # Operativa (OPERA), lo fuerza CrearMaquina.post en views.py.
    linea = forms.ChoiceField(label="Línea de Producción", required=False,
                              widget=forms.Select(attrs={"placeholder": "Selecciona línea"}))
    marca = forms.ChoiceField(label="Marca del Fabricante", required=False,
                              widget=forms.Select(attrs={"placeholder": "Selecciona marca"}))
    modelo = forms.ChoiceField(label="Modelo", required=False,
                               widget=forms.Select(attrs={"placeholder": "Selecciona modelo"}))
    tipo_maquina = forms.ChoiceField(label="Tipo de Máquina", required=False,
                                     widget=forms.Select(attrs={"placeholder": "Selecciona tipo"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        lineas = _fetch_catalogo("v1/linea/list/", "maquinaria_lineas_list")
        marcas = _fetch_catalogo("v1/marca/list/", "maquinaria_marcas_list")
        modelos = _fetch_catalogo("v1/modelo/list/", "maquinaria_modelos_list")
        tipos = _fetch_catalogo("v1/tipo_maquina/list/", "maquinaria_tipos_list")

        self.fields["linea"].choices = [("", "Seleccione")] + [
            (l["codigo"], l["nombre"]) for l in lineas if "codigo" in l
        ]
        self.fields["marca"].choices = [("", "Seleccione")] + [
            (m["clave"], m["nombre"]) for m in marcas if "clave" in m
        ]
        self.fields["modelo"].choices = [("", "Seleccione")] + [
            (m["codigo"], m["nombre"]) for m in modelos if "codigo" in m
        ]
        self.fields["tipo_maquina"].choices = [("", "Seleccione")] + [
            (t.get("numeroregistro"), t["nombre"]) for t in tipos if "nombre" in t
        ]

        # Se guarda el mapeo modelo->marca para poder validar la cascada
        # (que el modelo elegido sí pertenezca a la marca elegida) sin
        # tener que volver a pegarle al API en clean(), y también se lo
        # pasamos al widget para que cada <option> lleve su data-marca
        # (así el JS del template puede filtrar el <select> en el navegador).
        self._modelo_a_marca = {
            str(m["codigo"]): str(m.get("marca", ""))
            for m in modelos if "codigo" in m
        }
        self.fields["modelo"].widget = ModeloSelect(
            modelo_a_marca=self._modelo_a_marca,
            attrs={"placeholder": "Selecciona modelo"},
        )
        # Reasignamos choices porque el widget se reemplazó después de setearlas.
        self.fields["modelo"].widget.choices = self.fields["modelo"].choices

        for field_name, field in self.fields.items():
            if field_name not in ("imagen_url", "modelo_3d"):
                existing_classes = field.widget.attrs.get("class", "")
                field.widget.attrs["class"] = f"{existing_classes}".strip()

    def clean_codigo(self):
        codigo = self.cleaned_data.get("codigo", "")
        return codigo.strip().upper() or ""

    def clean_numeroserie(self):
        return self.cleaned_data.get("numeroserie", "").strip()

    def clean_modelo_3d(self):
        archivo = self.cleaned_data.get("modelo_3d")
        if archivo and not archivo.name.lower().endswith(".glb"):
            raise forms.ValidationError("El modelo 3D debe ser un archivo .glb.")
        return archivo

    def clean(self):
        cleaned = super().clean()
        marca = cleaned.get("marca")
        modelo = cleaned.get("modelo")
        if modelo and marca and self._modelo_a_marca.get(str(modelo)) not in (str(marca), ""):
            self.add_error("modelo", "Ese modelo no pertenece a la marca seleccionada.")
        return cleaned