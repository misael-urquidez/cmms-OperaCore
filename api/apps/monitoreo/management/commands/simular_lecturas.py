from django.core.management.base import BaseCommand

from apps.fallas.models import Maquina
from apps.monitoreo import services


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
            services.generar_lectura_simulada(maquina, probabilidad)
            self.stdout.write(f"{maquina.codigo}: lectura simulada registrada")
