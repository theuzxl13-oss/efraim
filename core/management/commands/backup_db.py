from datetime import datetime

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

BACKUP_DIR = settings.BASE_DIR / "backups"
MANTER_ULTIMOS = 30


class Command(BaseCommand):
    help = (
        "Cria um backup dos dados do sistema (congregações, membros, atas, eventos, "
        "usuários) em JSON e apaga backups com mais de %d execuções." % MANTER_ULTIMOS
    )

    def handle(self, *args, **options):
        BACKUP_DIR.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = BACKUP_DIR / f"backup_{stamp}.json"

        with open(path, "w", encoding="utf-8") as f:
            call_command(
                "dumpdata",
                "core",
                "auth.user",
                "auth.group",
                use_natural_foreign_keys=True,
                indent=2,
                stdout=f,
            )

        tamanho_kb = path.stat().st_size / 1024
        self.stdout.write(self.style.SUCCESS(f"Backup criado: {path} ({tamanho_kb:.1f} KB)"))

        backups = sorted(BACKUP_DIR.glob("backup_*.json"))
        antigos = backups[:-MANTER_ULTIMOS] if len(backups) > MANTER_ULTIMOS else []
        for arquivo in antigos:
            arquivo.unlink()
        if antigos:
            self.stdout.write(f"Removidos {len(antigos)} backup(s) antigo(s).")
