from django import template

register = template.Library()


@register.filter
def get_item(diccionario, clave):
    """Permite hacer {{ registro|get_item:campo_dinamico }} en el template,
    ya que Django no soporta 'registro[campo_dinamico]' directamente."""
    if not isinstance(diccionario, dict):
        return ""
    return diccionario.get(clave, "")


@register.filter
def pk_valor(registro, pk_field):
    """Si pk_field es lista (llave compuesta), junta los valores con '~'
    para poder mandarlos como un solo segmento de URL."""
    if isinstance(pk_field, (list, tuple)):
        return "~".join(str(registro.get(c, "")) for c in pk_field)
    return registro.get(pk_field, "")


@register.filter
def es_pk(nombre_campo, pk_field):
    """True si nombre_campo es (o forma parte de) el pk_field de la tabla,
    ya sea simple (string) o compuesto (lista)."""
    if isinstance(pk_field, (list, tuple)):
        return nombre_campo in pk_field
    return nombre_campo == pk_field


@register.filter
def si_no(valor):
    """Convierte 1/True a 'Sí' y 0/False a 'No'."""
    if valor in (1, "1", True, "true", "True"):
        return "Sí"
    elif valor in (0, "0", False, "false", "False"):
        return "No"
    return valor
