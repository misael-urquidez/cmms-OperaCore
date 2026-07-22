import random

from django.core.management.base import BaseCommand

from apps.fallas.models import Maquina
from apps.monitoreo.models import LecturaSensor
from apps.monitoreo.services import registrar_lectura


class Command(BaseCommand):
    help = "Genera una lectura simulada para cada máquina en modo simulado."

    def add_arguments(self, parser):
        parser.add_argument("--golpe-probabilidad", type=float, default=0.02)

    def handle(self, *args, **options):
        probabilidad = options["golpe_probabilidad"]
        if not 0 <= probabilidad <= 1:
            self.stderr.write("--golpe-probabilidad debe estar entre 0 y 1.")
            return
        maquinas = Maquina.objects.filter(modo_monitoreo="simulado")
        for maquina in maquinas:
            # La mayoría de lecturas quedan bajo el umbral; una minoría lo supera.
            fuera_de_rango = random.random() < 0.12
            vibracion = (
                random.uniform(maquina.umbral_vibracion * 1.05, maquina.umbral_vibracion * 1.6)
                if fuera_de_rango else random.uniform(0.1, maquina.umbral_vibracion * 0.85)
            )
            golpe = random.random() < probabilidad
            registrar_lectura(
                maquina=maquina, origen=LecturaSensor.ORIGEN_SIMULADO,
                vibracion=round(vibracion, 3), golpe=golpe,
                temperatura=round(random.uniform(20, 45), 1),
            )
            self.stdout.write(f"{maquina.codigo}: lectura simulada registrada")
