from datetime import date, datetime

from django.contrib import messages
from django.shortcuts import redirect, render

from .models import Herramienta, Movimiento, Refaccion


def listado_inventario(request):
    """Vista de listado: refacciones y herramientas, con alerta visual de stock bajo."""
    refacciones = Refaccion.objects.select_related('proveedor').all()
    herramientas = Herramienta.objects.select_related('tipo_herramienta').all()
    return render(request, 'inventario/list.html', {
        'refacciones': refacciones,
        'herramientas': herramientas,
    })


def registrar_movimiento(request):
    """Formulario para registrar una entrada o salida y actualizar el stock."""
    refacciones = Refaccion.objects.all()

    if request.method == 'POST':
        refaccion_id = request.POST.get('refaccion')
        tipo_movimiento = request.POST.get('tipo_movimiento')
        descripcion = request.POST.get('descripcion', '')

        try:
            cantidad = int(request.POST.get('cantidad', 0))
        except ValueError:
            cantidad = 0

        if cantidad <= 0:
            messages.error(request, 'La cantidad debe ser mayor a 0.')
            return render(request, 'inventario/movimiento_form.html', {'refacciones': refacciones})

        refaccion = Refaccion.objects.filter(pk=refaccion_id).first()
        if refaccion is None:
            messages.error(request, 'La refacción seleccionada no existe.')
            return render(request, 'inventario/movimiento_form.html', {'refacciones': refacciones})

        if tipo_movimiento == Movimiento.SALIDA and refaccion.stock < cantidad:
            messages.error(
                request,
                f'Stock insuficiente para "{refaccion.nombre}": hay '
                f'{refaccion.stock} unidades y se intentan sacar {cantidad}.'
            )
            return render(request, 'inventario/movimiento_form.html', {'refacciones': refacciones})

        Movimiento.objects.create(
            descripcion=descripcion,
            fecha=date.today(),
            hora=datetime.now().time(),
            tipo_movimiento=tipo_movimiento,
            refaccion=refaccion,
        )

        if tipo_movimiento == Movimiento.ENTRADA:
            refaccion.stock += cantidad
        else:
            refaccion.stock -= cantidad
        refaccion.save(update_fields=['stock'])

        messages.success(request, f'Movimiento de {tipo_movimiento.lower()} registrado correctamente.')
        return redirect('inventario-listado')

    return render(request, 'inventario/movimiento_form.html', {'refacciones': refacciones})
