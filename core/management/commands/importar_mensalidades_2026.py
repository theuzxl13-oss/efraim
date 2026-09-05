import datetime

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from core.models import Congregation, Mensalidade

# Meses (1-12) confirmados como pagos em 2026, migrados do controle em
# planilha usado pelo grupo antes deste sistema. Congregações não listadas
# aqui, ou meses fora da lista, ficam sem registro (aparecem como "aberto"
# ou "atrasado" automaticamente, conforme o mês).
MESES_PAGOS_2026 = {
    "Sede": range(1, 6),
    "Calu": range(1, 6),
    "Capela": range(1, 6),
    "Jacira": range(1, 6),
    "Cipó": range(1, 6),
    "Cerejeira": range(1, 6),
    "H. Azul": range(1, 5),
    "St. Julia": range(1, 7),
    "Itararé": range(1, 6),
    "Carmo 1": range(1, 4),
    "Penteado": range(3, 13),
    "Itororó": range(1, 3),
    # Crispim e Ch. Mel: nenhum mês confirmado como pago em 2026.
}

OBSERVACAO_MIGRACAO = "Migrado do controle em planilha usado pelo grupo antes deste sistema."
CONTEUDO_COMPROVANTE_PLACEHOLDER = (
    b"Registro historico migrado do controle em planilha anterior.\n"
    b"Sem comprovante digital disponivel para este mes."
)


class Command(BaseCommand):
    help = "Importa uma vez o historico de mensalidades pagas em 2026 vindo da planilha anterior."

    def handle(self, *args, **options):
        criados = 0
        ja_existiam = 0
        nao_encontradas = []

        for nome, meses in MESES_PAGOS_2026.items():
            try:
                congregacao = Congregation.objects.get(name__iexact=nome)
            except Congregation.DoesNotExist:
                nao_encontradas.append(nome)
                continue

            for mes in meses:
                mensalidade, criada = Mensalidade.objects.get_or_create(
                    congregation=congregacao,
                    mes_referencia=datetime.date(2026, mes, 1),
                    defaults={"confirmado": False, "observacoes": OBSERVACAO_MIGRACAO},
                )
                if not criada:
                    ja_existiam += 1
                    continue

                mensalidade.comprovante.save(
                    f"historico_{congregacao.id}_2026_{mes:02d}.pdf",
                    ContentFile(CONTEUDO_COMPROVANTE_PLACEHOLDER),
                    save=False,
                )
                mensalidade.confirmado = True
                mensalidade.save()
                criados += 1

        self.stdout.write(self.style.SUCCESS(f"{criados} mensalidade(s) criada(s) e confirmada(s)."))
        if ja_existiam:
            self.stdout.write(f"{ja_existiam} já existiam e foram mantidas como estavam (não sobrescritas).")
        if nao_encontradas:
            self.stdout.write(
                self.style.WARNING(
                    "Congregações não encontradas (confira o nome exato cadastrado): "
                    + ", ".join(nao_encontradas)
                )
            )
