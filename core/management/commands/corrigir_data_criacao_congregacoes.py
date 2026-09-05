import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Congregation

# Data segura, anterior a qualquer mes de mensalidade rastreado (2026) —
# evita que congregacoes reais (que existem desde antes deste sistema, mas
# so foram cadastradas aqui em 2026) tenham meses antigos escondidos como
# "ainda nao chegou o mes" na tabela de situacao das mensalidades.
DATA_SEGURA = datetime.date(2025, 1, 1)


class Command(BaseCommand):
    help = (
        "Ajusta a data de criacao das congregacoes ja cadastradas para uma data segura "
        "(2025-01-01), evitando que meses de 2026 antes do cadastro real no sistema "
        "aparecam incorretamente como 'ainda nao chegou o mes' em vez de atrasado/aberto."
    )

    def handle(self, *args, **options):
        data_hora = timezone.make_aware(datetime.datetime.combine(DATA_SEGURA, datetime.time.min))
        atualizadas = Congregation.objects.filter(created_at__gt=data_hora).update(created_at=data_hora)
        self.stdout.write(self.style.SUCCESS(f"{atualizadas} congregação(ões) ajustada(s)."))
