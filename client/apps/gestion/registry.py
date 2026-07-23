"""
Registro central del modulo Gestion.

Cada tabla administrable se describe con un dict. Para agregar una tabla
NUEVA no se toca views.py, urls.py ni los templates: solo se agrega su
config aca dentro del modulo correspondiente.

Estructura de un campo (dentro de "campos"):
    name        -> nombre que espera el API en el payload (POST)
    label       -> texto que se muestra en la UI
    tipo        -> "text" | "textarea" | "int" | "float" | "date" | "time" | "select"
    requerido   -> True/False (valida en servidor antes de mandar al API)
    columna     -> True/False, si aparece como columna en el listado.
                   IMPORTANTE: los "List...Serializer" del api casi siempre
                   regresan MENOS campos que el modelo completo. Solo marca
                   columna=True en campos que el endpoint de list SI regresa,
                   si no, la columna sale vacia.
    fk          -> (opcional) slug de OTRA tabla del registro. El campo se
                   pinta como <select> cuyas opciones se llenan pidiendo el
                   listado de esa tabla.
    fk_value    -> atributo pk de la tabla referenciada (ej "codigo")
    fk_label    -> atributo a mostrar en el <option> (ej "nombre")

Estructura de una tabla:
    slug        -> identificador unico usado en la URL /gestion/<slug>/
    label       -> nombre visible
    modulo      -> agrupador visual en el index de Gestion
    api_app     -> namespace del api (settings.API_BASE_URL/<api_app>)
    list_path   -> ruta relativa GET para listar
    create_path -> ruta relativa POST para crear
    pk_field    -> campo que la tabla usa como identificador visual (columna "ID")
    campos      -> lista de campos, en el mismo orden que espera el
                   Create...Serializer del api (solo por claridad)

Claves opcionales para habilitar Editar / Eliminar (si no se ponen, esas
acciones simplemente no aparecen en la UI para esa tabla):
    detail_path   -> ruta GET de un registro. Usa "{pk}" como placeholder,
                      ej "v1/planta/{pk}/". Se usa para precargar el form.
    update_path   -> ruta PUT/PATCH para editar. Si no se especifica pero
                      si hay detail_path, se reusa detail_path (caso de las
                      RetrieveUpdateDestroyAPIView de inventario/fallas).
    update_method -> "PUT" o "PATCH" (default "PATCH")
    delete_path   -> ruta DELETE. Si no se especifica, no hay boton borrar
                      para esa tabla (ej. maquinaria, que hoy no expone
                      destroy en el api).
    delete_method -> default "DELETE"

NOTA: Inventario ya tiene create/list/detail/update/delete funcionando
(RetrieveUpdateDestroyAPIView), Fallas igual para sus catalogos desde que
se le agregaron las vistas de detalle. Antes de registrar una tabla nueva
aqui, confirma que su endpoint list/create ya responda 200 pegandole con
curl o Postman.
"""

GESTION_REGISTRY = {

    # ------------------------------------------------------- MAQUINARIA ---
    "planta": {
        "slug": "planta",
        "label": "Plantas",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/planta/list/",
        "create_path": "v1/planta/create/",
        "detail_path": "v1/planta/{pk}/",
        "update_path": "v1/planta/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
            {"name": "telefono", "label": "Teléfono", "tipo": "text", "requerido": True, "columna": False},
            {"name": "dircalle", "label": "Calle", "tipo": "text", "requerido": True, "columna": False},
            {"name": "dircodigopostal", "label": "Código postal", "tipo": "text", "requerido": True, "columna": False},
            {"name": "dirnumero", "label": "Número", "tipo": "text", "requerido": True, "columna": False},
        ],
    },

    "area": {
        "slug": "area",
        "label": "Áreas",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/area/list/",
        "create_path": "v1/area/create/",
        "detail_path": "v1/area/{pk}/",
        "update_path": "v1/area/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
            {"name": "telefono", "label": "Teléfono", "tipo": "text", "requerido": True, "columna": False},
            {"name": "planta", "label": "Planta", "tipo": "select", "requerido": True, "columna": True,
             "fk": "planta", "fk_value": "codigo", "fk_label": "nombre"},
        ],
    },

    "edo-maquina": {
        "slug": "edo-maquina",
        "label": "Estados de máquina",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/edo_maquina/list/",
        "create_path": "v1/edo_maquina/create/",
        "detail_path": "v1/edo_maquina/{pk}/",
        "update_path": "v1/edo_maquina/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },

    "linea": {
        "slug": "linea",
        "label": "Líneas",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/linea/list/",
        "create_path": "v1/linea/create/",
        "detail_path": "v1/linea/{pk}/",
        "update_path": "v1/linea/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
            # El list de Linea NO regresa "area" (solo codigo/nombre), por eso
            # columna=False aqui aunque si se manda al crear.
            {"name": "area", "label": "Área", "tipo": "select", "requerido": True, "columna": False,
             "fk": "area", "fk_value": "codigo", "fk_label": "nombre"},
        ],
    },

    "marca": {
        "slug": "marca",
        "label": "Marcas",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/marca/list/",
        "create_path": "v1/marca/create/",
        "detail_path": "v1/marca/{pk}/",
        "update_path": "v1/marca/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "clave",
        "campos": [
            {"name": "clave", "label": "Clave", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },

    "modelo": {
        "slug": "modelo",
        "label": "Modelos",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/modelo/list/",
        "create_path": "v1/modelo/create/",
        "detail_path": "v1/modelo/{pk}/",
        "update_path": "v1/modelo/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
            {"name": "marca", "label": "Marca", "tipo": "select", "requerido": True, "columna": True,
             "fk": "marca", "fk_value": "clave", "fk_label": "nombre"},
        ],
    },

    "tipo-maquina": {
        "slug": "tipo-maquina",
        "label": "Tipos de máquina",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/tipo_maquina/list/",
        "create_path": "v1/tipo_maquina/create/",
        "detail_path": "v1/tipo_maquina/{pk}/",
        "update_path": "v1/tipo_maquina/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "numeroregistro",
        "campos": [
            # El Create...Serializer de TipoMaquina NO acepta pk manual,
            # se autogenera en el api. Por eso no se manda "numeroregistro".
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },

    "maquina": {
        "slug": "maquina",
        "label": "Máquinas",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/maquina/list/",
        "create_path": "v1/maquina/create/",
        "detail_path": "v1/maquina/{pk}/",
        "update_path": "v1/maquina/update/{pk}/",
        "update_method": "PUT",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "numeroserie", "label": "Número de serie", "tipo": "text", "requerido": False, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
            {"name": "imagen_url", "label": "URL de imagen", "tipo": "text", "requerido": False, "columna": True},
            {"name": "fechainstalacion", "label": "Fecha de instalación", "tipo": "date", "requerido": True, "columna": False},
            {"name": "linea", "label": "Línea", "tipo": "select", "requerido": False, "columna": False,
             "fk": "linea", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "marca", "label": "Marca", "tipo": "select", "requerido": False, "columna": True,
             "fk": "marca", "fk_value": "clave", "fk_label": "nombre"},
            {"name": "modelo", "label": "Modelo", "tipo": "select", "requerido": False, "columna": True,
             "fk": "modelo", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "estado_maquina", "label": "Estado de máquina", "tipo": "select", "requerido": False, "columna": True,
             "fk": "edo-maquina", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "tipo_maquina", "label": "Tipo de máquina", "tipo": "select", "requerido": False, "columna": True,
             "fk": "tipo-maquina", "fk_value": "numeroregistro", "fk_label": "nombre"},
        ],
    },
    "registro-ops": {
        "slug": "registro-ops",
        "label": "Registro de Operaciones de Maquinaria",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/registro-ops/list/",
        "create_path": "v2/registro-ops/create/",
        "detail_path": "v1/registro-ops/{pk}/",
        "update_path": "v1/registro-ops/{pk}/",
        "update_method": "PUT",
        "delete_path": "v1/registro-ops/{pk}/",
        "delete_method": "DELETE",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "fechainicio", "label": "Fecha Inicio", "tipo": "date", "requerido": True, "columna": True},
            {"name": "fechafin", "label": "Fecha Fin", "tipo": "date", "requerido": True, "columna": True},
            {"name": "horasoperacion", "label": "Horas de Operación", "tipo": "int", "requerido": True, "columna": True},
            {"name": "maquina", "label": "Máquina", "tipo": "select", "requerido": True, "columna": True, "fk": "maquina", "fk_value": "codigo", "fk_label": "nombre"},
        ],
    },
    # ------------------------------------------------------ INDICADORES ---
    "indicador": {
        "slug": "indicador",
        "label": "Indicadores",
        "modulo": "Maquinaria",
        "api_app": "maquinaria",
        "list_path": "v1/indicador/list/",
        "create_path": "v2/indicador/create/",
        "detail_path": "v1/indicador/{pk}/",
        "update_path": "v1/indicador/{pk}/",
        "update_method": "PUT",
        "delete_path": "v1/indicador/{pk}/",
        "delete_method": "DELETE",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "maquina", "label": "Máquina", "tipo": "select", "requerido": True, "columna": True, "fk": "maquina", "fk_value": "codigo", "fk_label": "nombre", },
            {"name": "fechainicio", "label": "Fecha Inicio", "tipo": "date", "requerido": True, "columna": True, },
            { "name": "fechafin", "label": "Fecha Fin", "tipo": "date", "requerido": True, "columna": True, },
            { "name": "mttr", "label": "MTTR (Horas)", "tipo": "float", "requerido": True, "columna": False, },
            { "name": "mtbf", "label": "MTBF (Horas)", "tipo": "float", "requerido": True, "columna": False, },
            { "name": "porcentajedispo", "label": "Disponibilidad (%)", "tipo": "float", "requerido": True, "columna": True,},
        ],
    },
    # ------------------------------------------------------------ FALLAS ---
    "tipo-severidad": {
        "slug": "tipo-severidad",
        "label": "Tipos de severidad",
        "modulo": "Fallas",
        "api_app": "fallas",
        "list_path": "v1/tipos-severidad/",
        "create_path": "v2/tipos-severidad/create/",
        "detail_path": "v2/tipos-severidad/{pk}/",
        "delete_path": "v2/tipos-severidad/{pk}/",
        "pk_field": "codigo",
        "invalidate_cache_keys": ["fallas_severidades"],
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "tipo-falla": {
        "slug": "tipo-falla",
        "label": "Tipos de falla",
        "modulo": "Fallas",
        "api_app": "fallas",
        "list_path": "v1/tipos-falla/",
        "create_path": "v2/tipos-falla/create/",
        "detail_path": "v2/tipos-falla/{pk}/",
        "delete_path": "v2/tipos-falla/{pk}/",
        "pk_field": "numeroRegistro",
        "invalidate_cache_keys": ["fallas_tipos_falla"],
        "campos": [
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "edo-reporte": {
        "slug": "edo-reporte",
        "label": "Estados de reporte",
        "modulo": "Fallas",
        "api_app": "fallas",
        "list_path": "v1/estados-reporte/",
        "create_path": "v2/estados-reporte/create/",
        "detail_path": "v2/estados-reporte/{pk}/",
        "delete_path": "v2/estados-reporte/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "tipo-reporte": {
        # PK compuesta: (tipo_falla, reporte_falla). "reporte_falla" es
        # texto libre a proposito: REPORTE_FALLA no esta en Gestion (ver
        # nota "Lo que NO va en Gestión" en el plan original), asi que no
        # hay catalogo del que sacar un <select> de opciones; el usuario
        # captura a mano el numeroRegistro del reporte.
        "slug": "tipo-reporte",
        "label": "Tipos de falla por reporte",
        "modulo": "Fallas",
        "api_app": "fallas",
        "list_path": "v1/tipo-reporte/list/",
        "create_path": "v2/tipo-reporte/create/",
        "detail_path": "v1/tipo-reporte/{tipo_falla}/{reporte_falla}/",
        "delete_path": "v1/tipo-reporte/{tipo_falla}/{reporte_falla}/",
        "pk_field": ["tipo_falla", "reporte_falla"],
        "pk_label": "Tipo de falla / Reporte",
        "campos": [
            {"name": "tipo_falla", "label": "Tipo de falla", "tipo": "select", "requerido": True, "columna": True,
             "fk": "tipo-falla", "fk_value": "numeroRegistro", "fk_label": "nombre"},
            {"name": "reporte_falla", "label": "Reporte (número de registro)", "tipo": "int", "requerido": True, "columna": True},
        ],
    },

    # -------------------------------------------------------- INVENTARIO ---
    # Estas 8 ya tienen list/create/detail(RetrieveUpdateDestroy) probados
    # en api/apps/inventario/{views,urls}.py, por eso salen con CRUD completo.
    "clasificacion": {
        "slug": "clasificacion",
        "label": "Clasificaciones",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/clasificaciones/list/",
        "create_path": "v2/clasificaciones/create/",
        "detail_path": "v1/clasificaciones/{pk}/",
        "delete_path": "v1/clasificaciones/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "edo-herramienta": {
        "slug": "edo-herramienta",
        "label": "Estados de herramienta",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/estados-herramienta/list/",
        "create_path": "v2/estados-herramienta/create/",
        "detail_path": "v1/estados-herramienta/{pk}/",
        "delete_path": "v1/estados-herramienta/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "edo-pieza": {
        "slug": "edo-pieza",
        "label": "Estados de pieza",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/estados-pieza/list/",
        "create_path": "v2/estados-pieza/create/",
        "detail_path": "v1/estados-pieza/{pk}/",
        "delete_path": "v1/estados-pieza/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "edo-refaccion": {
        "slug": "edo-refaccion",
        "label": "Estados de refacción",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/estados-refaccion/list/",
        "create_path": "v2/estados-refaccion/create/",
        "detail_path": "v1/estados-refaccion/{pk}/",
        "delete_path": "v1/estados-refaccion/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "tipo-herramienta": {
        "slug": "tipo-herramienta",
        "label": "Tipos de herramienta",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/tipos-herramienta/list/",
        "create_path": "v2/tipos-herramienta/create/",
        "detail_path": "v1/tipos-herramienta/{pk}/",
        "delete_path": "v1/tipos-herramienta/{pk}/",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "tipo-pieza": {
        "slug": "tipo-pieza",
        "label": "Tipos de pieza",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/tipos-pieza/list/",
        "create_path": "v2/tipos-pieza/create/",
        "detail_path": "v1/tipos-pieza/{pk}/",
        "delete_path": "v1/tipos-pieza/{pk}/",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "tipo-refaccion": {
        "slug": "tipo-refaccion",
        "label": "Tipos de refacción",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/tipos-refaccion/list/",
        "create_path": "v2/tipos-refaccion/create/",
        "detail_path": "v1/tipos-refaccion/{pk}/",
        "delete_path": "v1/tipos-refaccion/{pk}/",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "proveedor": {
        "slug": "proveedor",
        "label": "Proveedores",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/proveedores/list/",
        "create_path": "v2/proveedores/create/",
        "detail_path": "v1/proveedores/{pk}/",
        "delete_path": "v1/proveedores/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "rfc", "label": "RFC", "tipo": "text", "requerido": True, "columna": True},
            {"name": "razonsocial", "label": "Razón social", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombrecomercial", "label": "Nombre comercial", "tipo": "text", "requerido": True, "columna": False},
            {"name": "telefono", "label": "Teléfono", "tipo": "text", "requerido": True, "columna": True},
            {"name": "email", "label": "Email", "tipo": "text", "requerido": True, "columna": False},
            {"name": "dircalle", "label": "Calle", "tipo": "text", "requerido": True, "columna": False},
            {"name": "dircodigopostal", "label": "Código postal", "tipo": "text", "requerido": True, "columna": False},
            {"name": "dirnumero", "label": "Número", "tipo": "text", "requerido": True, "columna": False},
            {"name": "contnombre", "label": "Contacto - nombre", "tipo": "text", "requerido": True, "columna": False},
            {"name": "contapellpat", "label": "Contacto - apellido paterno", "tipo": "text", "requerido": True, "columna": False},
            {"name": "contapellmat", "label": "Contacto - apellido materno", "tipo": "text", "requerido": False, "columna": False},
        ],
    },
    "herramienta": {
        "slug": "herramienta",
        "label": "Herramientas",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/herramientas/list/",
        "create_path": "v2/herramientas/create/",
        "detail_path": "v1/herramientas/{pk}/",
        "delete_path": "v1/herramientas/{pk}/",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
            {"name": "imagen", "label": "URL de imagen", "tipo": "text", "requerido": False, "columna": False},
            {"name": "tipo_herramienta", "label": "Tipo de herramienta", "tipo": "select", "requerido": False, "columna": True,
             "fk": "tipo-herramienta", "fk_value": "numeroregistro", "fk_label": "nombre"},
        ],
    },
    "pieza": {
        "slug": "pieza",
        "label": "Piezas",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/piezas/list/",
        "create_path": "v2/piezas/create/",
        "detail_path": "v1/piezas/{pk}/",
        "delete_path": "v1/piezas/{pk}/",
        "pk_field": "numeroserie",
        "campos": [
            {"name": "numeroserie", "label": "Número de serie", "tipo": "text", "requerido": True, "columna": True},
            {"name": "codigoetiqueta", "label": "Código de etiqueta", "tipo": "text", "requerido": False, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "costoinicial", "label": "Costo inicial", "tipo": "float", "requerido": True, "columna": False},
            {"name": "horasoperacion", "label": "Horas de operación", "tipo": "int", "requerido": False, "columna": False},
            {"name": "tiempovidautil", "label": "Vida útil (meses)", "tipo": "int", "requerido": True, "columna": False},
            {"name": "depresacionanual", "label": "Depreciación anual", "tipo": "float", "requerido": False, "columna": False},
            {"name": "valorresidual", "label": "Valor residual", "tipo": "float", "requerido": False, "columna": False},
            {"name": "fechainstalacion", "label": "Fecha de instalación", "tipo": "date", "requerido": True, "columna": False},
            {"name": "fechagarantia", "label": "Fecha de garantía", "tipo": "date", "requerido": False, "columna": False},
            {"name": "edo_pieza", "label": "Estado", "tipo": "select", "requerido": False, "columna": True,
             "fk": "edo-pieza", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "maquina", "label": "Máquina", "tipo": "select", "requerido": False, "columna": True,
             "fk": "maquina", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "tipo_pieza", "label": "Tipo de pieza", "tipo": "select", "requerido": False, "columna": False,
             "fk": "tipo-pieza", "fk_value": "numeroregistro", "fk_label": "nombre"},
        ],
    },
    "refaccion": {
        "slug": "refaccion",
        "label": "Refacciones",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/refacciones/list/",
        "create_path": "v2/refacciones/create/",
        "detail_path": "v1/refacciones/{pk}/",
        "delete_path": "v1/refacciones/{pk}/",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "codigosku", "label": "SKU", "tipo": "text", "requerido": True, "columna": True},
            {"name": "puntoreorden", "label": "Punto de reorden", "tipo": "int", "requerido": False, "columna": False},
            {"name": "codigoinventario", "label": "Código de inventario", "tipo": "text", "requerido": True, "columna": False},
            {"name": "numeroorden", "label": "Número de orden", "tipo": "text", "requerido": True, "columna": False},
            {"name": "costo", "label": "Costo", "tipo": "float", "requerido": True, "columna": False},
            {"name": "tiempoentregaapr", "label": "Tiempo de entrega aprox. (días)", "tipo": "int", "requerido": False, "columna": False},
            {"name": "stock", "label": "Stock", "tipo": "int", "requerido": True, "columna": True},
            {"name": "stockminimo", "label": "Stock mínimo", "tipo": "int", "requerido": True, "columna": False},
            {"name": "proveedor", "label": "Proveedor", "tipo": "select", "requerido": False, "columna": True,
             "fk": "proveedor", "fk_value": "codigo", "fk_label": "razonsocial"},
            {"name": "tipo_refaccion", "label": "Tipo de refacción", "tipo": "select", "requerido": False, "columna": False,
             "fk": "tipo-refaccion", "fk_value": "numeroregistro", "fk_label": "nombre"},
            {"name": "clasificacion", "label": "Clasificación", "tipo": "select", "requerido": False, "columna": False,
             "fk": "clasificacion", "fk_value": "codigo", "fk_label": "nombre"},
        ],
    },
    "refacc-maqui": {
        # PK compuesta: (maquina, refaccion). Catalogo de que refacciones
        # aplican a cada maquina.
        "slug": "refacc-maqui",
        "label": "Refacciones por máquina",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/refacc-maqui/list/",
        "create_path": "v2/refacc-maqui/create/",
        "detail_path": "v1/refacc-maqui/{maquina}/{refaccion}/",
        "delete_path": "v1/refacc-maqui/{maquina}/{refaccion}/",
        "pk_field": ["maquina", "refaccion"],
        "pk_label": "Máquina / Refacción",
        "campos": [
            {"name": "maquina", "label": "Máquina", "tipo": "select", "requerido": True, "columna": True,
             "fk": "maquina", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "refaccion", "label": "Refacción", "tipo": "select", "requerido": True, "columna": True,
             "fk": "refaccion", "fk_value": "numeroregistro", "fk_label": "nombre"},
        ],
    },
    "existencia-herramienta": {
        # PK compuesta: (herramienta, edo_herramienta). Cuenta cuantas
        # unidades de una herramienta hay en cada estado (nueva, en uso,
        # dañada, etc). No confundir con el catalogo "edo-herramienta".
        "slug": "existencia-herramienta",
        "label": "Existencias de herramienta",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/existencia-herramienta/list/",
        "create_path": "v2/existencia-herramienta/create/",
        "detail_path": "v1/existencia-herramienta/{herramienta}/{edo_herramienta}/",
        "delete_path": "v1/existencia-herramienta/{herramienta}/{edo_herramienta}/",
        "pk_field": ["herramienta", "edo_herramienta"],
        "pk_label": "Herramienta / Estado",
        "campos": [
            {"name": "herramienta", "label": "Herramienta", "tipo": "select", "requerido": True, "columna": True,
             "fk": "herramienta", "fk_value": "numeroregistro", "fk_label": "nombre"},
            {"name": "edo_herramienta", "label": "Estado", "tipo": "select", "requerido": True, "columna": True,
             "fk": "edo-herramienta", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "cantidad", "label": "Cantidad", "tipo": "int", "requerido": True, "columna": True},
        ],
    },
    "existencia-refaccion": {
        # PK compuesta: (estado_refaccion, refaccion). Analogo al anterior
        # pero para refacciones.
        "slug": "existencia-refaccion",
        "label": "Existencias de refacción",
        "modulo": "Inventario",
        "api_app": "inventario",
        "list_path": "v1/existencia-refaccion/list/",
        "create_path": "v2/existencia-refaccion/create/",
        "detail_path": "v1/existencia-refaccion/{estado_refaccion}/{refaccion}/",
        "delete_path": "v1/existencia-refaccion/{estado_refaccion}/{refaccion}/",
        "pk_field": ["estado_refaccion", "refaccion"],
        "pk_label": "Estado / Refacción",
        "campos": [
            {"name": "estado_refaccion", "label": "Estado", "tipo": "select", "requerido": True, "columna": True,
             "fk": "edo-refaccion", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "refaccion", "label": "Refacción", "tipo": "select", "requerido": True, "columna": True,
             "fk": "refaccion", "fk_value": "numeroregistro", "fk_label": "nombre"},
            {"name": "cantidad", "label": "Cantidad", "tipo": "int", "requerido": True, "columna": True},
        ],
    },

    # -------------------------------------------------------- USUARIOS ---
    "rol": {
        "slug": "rol",
        "label": "Roles",
        "modulo": "Usuarios",
        "api_app": "usuarios",
        "list_path": "roles/",
        "create_path": "roles/create/",
        "detail_path": "roles/{pk}/",
        "delete_path": "roles/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "especialidad": {
        "slug": "especialidad",
        "label": "Especialidades",
        "modulo": "Usuarios",
        "api_app": "usuarios",
        "list_path": "especialidades/",
        "create_path": "especialidades/create/",
        "detail_path": "especialidades/{pk}/",
        "delete_path": "especialidades/{pk}/",
        "pk_field": "numeroRegistro",
        "campos": [
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },

    "trabajador": {
        "slug": "trabajador",
        "label": "Trabajadores",
        "modulo": "Usuarios",
        "api_app": "usuarios",
        "list_path": "v1/trabajadores/list/",
        "create_path": "registro/",              # <- el endpoint que YA EXISTE
        "detail_path": "v1/trabajadores/{pk}/",
        "update_path": "v1/trabajadores/{pk}/",
        "update_method": "PATCH",
        # sin delete_path a propósito, ver nota en views.py de la API
        # (Trabajador no se borra fisico, se da de baja con 'actividad')
        "pk_field": "numeroNomina",
        "campos": [
            {"name": "numeroNomina", "label": "Número de nómina", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "apellidoPat", "label": "Apellido paterno", "tipo": "text", "requerido": True, "columna": True},
            {"name": "apellidoMat", "label": "Apellido materno", "tipo": "text", "requerido": False, "columna": False},
            {"name": "telefono", "label": "Teléfono", "tipo": "text", "requerido": True, "columna": False},
            {"name": "correo", "label": "Correo", "tipo": "text", "requerido": True, "columna": True},
            {"name": "usuario", "label": "Usuario", "tipo": "text", "requerido": True, "columna": True},
            {"name": "password", "label": "Contraseña", "tipo": "password", "requerido": True, "columna": False},
            {"name": "password2", "label": "Confirmar contraseña", "tipo": "password", "requerido": True, "columna": False},
            {"name": "rol", "label": "Rol", "tipo": "select", "requerido": False, "columna": True,
             "fk": "rol", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "especialidad", "label": "Especialidad", "tipo": "select", "requerido": False, "columna": False,
             "fk": "especialidad", "fk_value": "codigo", "fk_label": "nombre"},
        ],
    },

    # ---------------------------------------------------- MANTENIMIENTO ---
    "estado-orden": {
        "slug": "estado-orden",
        "label": "Estados de orden",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/estado-orden/list/",
        "create_path": "v2/estado-orden/create/",
        "detail_path": "v1/estado-orden/{pk}/",
        "delete_path": "v1/estado-orden/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "tipo-mantenimiento": {
        "slug": "tipo-mantenimiento",
        "label": "Tipos de mantenimiento",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/tipo-mantenimiento/list/",
        "create_path": "v2/tipo-mantenimiento/create/",
        "detail_path": "v1/tipo-mantenimiento/{pk}/",
        "delete_path": "v1/tipo-mantenimiento/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "nombre", "label": "Nombre", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "tarea": {
        "slug": "tarea",
        "label": "Tareas",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/tareas/list/",
        "create_path": "v2/tareas/create/",
        "detail_path": "v1/tareas/{pk}/",
        "delete_path": "v1/tareas/{pk}/",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "instruccion", "label": "Instrucción", "tipo": "text", "requerido": True, "columna": True},
            {"name": "actividad", "label": "¿Activa? (1 = sí, 0 = no)", "tipo": "int", "requerido": True, "columna": True},
        ],
    },
    "tipo-movimiento": {
        "slug": "tipo-movimiento",
        "label": "Tipos de movimiento",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/tipo-movimiento/list/",
        "create_path": "v2/tipo-movimiento/create/",
        "detail_path": "v1/tipo-movimiento/{pk}/",
        "delete_path": "v1/tipo-movimiento/{pk}/",
        "pk_field": "codigo",
        "campos": [
            {"name": "codigo", "label": "Código", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": False, "columna": True},
        ],
    },
    "tarea-orden": {
        # PK compuesta: (tarea, orden_mantenimiento). "orden_mantenimiento"
        # es texto libre a proposito: ORDEN_MANTENIMIENTO no esta en
        # Gestion (necesita vista maestro-detalle a mano, ver plan
        # original), asi que no hay catalogo del que sacar un <select>;
        # el usuario captura a mano el folio de la orden.
        "slug": "tarea-orden",
        "label": "Tareas por orden",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/tarea-orden/list/",
        "create_path": "v2/tarea-orden/create/",
        "detail_path": "v1/tarea-orden/{tarea}/{orden_mantenimiento}/",
        "delete_path": "v1/tarea-orden/{tarea}/{orden_mantenimiento}/",
        "pk_field": ["tarea", "orden_mantenimiento"],
        "pk_label": "Tarea / Orden",
        "campos": [
            {"name": "tarea", "label": "Tarea", "tipo": "select", "requerido": True, "columna": True,
             "fk": "tarea", "fk_value": "numeroregistro", "fk_label": "instruccion"},
            {"name": "orden_mantenimiento", "label": "Orden (folio)", "tipo": "text", "requerido": True, "columna": True},
            {"name": "fechainicio", "label": "Fecha de inicio", "tipo": "date", "requerido": True, "columna": True},
            {"name": "fechacierre", "label": "Fecha de cierre", "tipo": "date", "requerido": False, "columna": False},
            {"name": "horainicio", "label": "Hora de inicio", "tipo": "time", "requerido": True, "columna": False},
            {"name": "horafin", "label": "Hora de fin", "tipo": "time", "requerido": False, "columna": False},
            {"name": "verificacion", "label": "¿Verificado? (1 = sí, 0 = no)", "tipo": "int", "requerido": False, "columna": True},
            {"name": "observaciones", "label": "Observaciones", "tipo": "textarea", "requerido": False, "columna": False},
        ],
    },
    "herra-orden": {
        # PK compuesta: (herramienta, orden_mantenimiento).
        "slug": "herra-orden",
        "label": "Herramientas por orden",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/herra-orden/list/",
        "create_path": "v2/herra-orden/create/",
        "detail_path": "v1/herra-orden/{herramienta}/{orden_mantenimiento}/",
        "delete_path": "v1/herra-orden/{herramienta}/{orden_mantenimiento}/",
        "pk_field": ["herramienta", "orden_mantenimiento"],
        "pk_label": "Herramienta / Orden",
        "campos": [
            {"name": "herramienta", "label": "Herramienta", "tipo": "select", "requerido": True, "columna": True,
             "fk": "herramienta", "fk_value": "numeroregistro", "fk_label": "nombre"},
            {"name": "orden_mantenimiento", "label": "Orden (folio)", "tipo": "text", "requerido": True, "columna": True},
        ],
    },
    "trabajador-orden": {
        # PK compuesta: (trabajador, orden_mantenimiento).
        "slug": "trabajador-orden",
        "label": "Personal asignado a orden",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/traba-orden-personal/list/",
        "create_path": "v2/traba-orden-personal/create/",
        "detail_path": "v1/traba-orden-personal/{trabajador}/{orden_mantenimiento}/",
        "delete_path": "v1/traba-orden-personal/{trabajador}/{orden_mantenimiento}/",
        "pk_field": ["trabajador", "orden_mantenimiento"],
        "pk_label": "Trabajador / Orden",
        "campos": [
            {"name": "trabajador", "label": "Trabajador", "tipo": "select", "requerido": True, "columna": True,
             "fk": "trabajador", "fk_value": "numeroNomina", "fk_label": "nombre"},
            {"name": "orden_mantenimiento", "label": "Orden (folio)", "tipo": "text", "requerido": True, "columna": True},
        ],
    },
    "movimiento": {
        "slug": "movimiento",
        "label": "Movimientos de almacén / refacciones",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/movimiento/list/",
        "create_path": "v2/movimiento/create/",
        "detail_path": "v1/movimiento/{pk}/",
        "update_path": "v1/movimiento/{pk}/",
        "update_method": "PUT",
        "delete_path": "v1/movimiento/{pk}/",
        "delete_method": "DELETE",
        "pk_field": "numeroregistro",
        "campos": [
            {"name": "descripcion", "label": "Descripción", "tipo": "text", "requerido": True, "columna": False},
            {"name": "fecha", "label": "Fecha", "tipo": "date", "requerido": True, "columna": True},
            {"name": "hora", "label": "Hora", "tipo": "text", "requerido": True, "columna": True},
            {"name": "tipomovimiento", "label": "Tipo de Movimiento", "tipo": "select", "requerido": True, "columna": True, "fk": "tipo-movimiento", "fk_value": "codigo", "fk_label": "descripcion"},
            {"name": "orden_mantenimiento", "label": "Orden de Mantenimiento (Folio)", "tipo": "select", "requerido": False, "columna": True, "fk": "orden-mantenimiento", "fk_value": "folio", "fk_label": "folio"},
            {"name": "refaccion", "label": "Refacción", "tipo": "select", "requerido": False, "columna": False, "fk": "refaccion", "fk_value": "numeroregistro", "fk_label": "nombre"},
            {"name": "pieza", "label": "Pieza", "tipo": "select", "requerido": False, "columna": False, "fk": "pieza", "fk_value": "codigo", "fk_label": "nombre"},
        ],
    },
    "orden-mantenimiento": {
        "slug": "orden-mantenimiento",
        "label": "Órdenes de Mantenimiento",
        "modulo": "Mantenimiento",
        "api_app": "mantenimiento",
        "list_path": "v1/orden-mantenimiento/list/",
        "create_path": "v2/orden-mantenimiento/create/",
        "detail_path": "v1/orden-mantenimiento/{pk}/",
        "update_path": "v1/orden-mantenimiento/{pk}/",
        "update_method": "PUT",
        "delete_path": "v1/orden-mantenimiento/{pk}/",
        "delete_method": "DELETE",
        "pk_field": "folio",
        "campos": [
            {"name": "folio", "label": "Folio", "tipo": "text", "requerido": True, "columna": True},
            {"name": "descripcion", "label": "Descripción", "tipo": "textarea", "requerido": True, "columna": False},
            {"name": "diagnostico", "label": "Diagnóstico", "tipo": "textarea", "requerido": False, "columna": False},
            {"name": "notas", "label": "Notas", "tipo": "textarea", "requerido": False, "columna": False},
            {"name": "fechaprogramada", "label": "Fecha Programada", "tipo": "date", "requerido": False, "columna": False},
            {"name": "fechacreacion", "label": "Fecha Creación", "tipo": "date", "requerido": True, "columna": True},
            {"name": "horacreacion", "label": "Hora Creación", "tipo": "text", "requerido": False, "columna": False},
            {"name": "fechacierre", "label": "Fecha Cierre", "tipo": "date", "requerido": False, "columna": False},
            {"name": "horacierre", "label": "Hora Cierre", "tipo": "text", "requerido": False, "columna": False},
            {"name": "horasintervenidas", "label": "Horas Intervenidas", "tipo": "int", "requerido": False, "columna": False},
            {"name": "porcentaje", "label": "Porcentaje de Avance", "tipo": "int", "requerido": False, "columna": True},
            {"name": "imagen", "label": "Imagen / Evidencia", "tipo": "text", "requerido": False, "columna": False},
            {"name": "maquina", "label": "Máquina", "tipo": "select", "requerido": True, "columna": True, "fk": "maquina", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "trabajador", "label": "Trabajador Asignado", "tipo": "select", "requerido": False, "columna": False, "fk": "trabajador", "fk_value": "numeroNomina", "fk_label": "nombre"},
            {"name": "reporte_falla", "label": "Reporte de Falla", "tipo": "select", "requerido": False, "columna": False, "fk": "reporte-falla", "fk_value": "numeroregistro", "fk_label": "descripcion"},
            {"name": "tipo_mantenimiento", "label": "Tipo de Mantenimiento", "tipo": "select", "requerido": True, "columna": True, "fk": "tipo-mantenimiento", "fk_value": "codigo", "fk_label": "nombre"},
            {"name": "estado_orden", "label": "Estado de la Orden", "tipo": "select", "requerido": True, "columna": True, "fk": "estado-orden", "fk_value": "codigo", "fk_label": "nombre"},
        ],
    },
}


def get_tabla(slug):
    return GESTION_REGISTRY.get(slug)


def get_modulos():
    """Agrupa el registro por 'modulo' para pintar el index de Gestion."""
    modulos = {}
    for config in GESTION_REGISTRY.values():
        modulos.setdefault(config["modulo"], []).append(config)
    return dict(sorted(modulos.items()))
