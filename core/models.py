from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Congregation(models.Model):
    name = models.CharField("Nome da congregação", max_length=150, unique=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Congregação"
        verbose_name_plural = "Congregações"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        verbose_name="Usuário",
    )
    congregation = models.ForeignKey(
        Congregation,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="admins",
        verbose_name="Congregação",
        help_text="Deixe em branco para acesso geral (todas as congregações).",
    )

    class Meta:
        verbose_name = "Perfil de administrador"
        verbose_name_plural = "Perfis de administradores"

    def __str__(self):
        escopo = self.congregation.name if self.congregation_id else "Geral (todas as congregações)"
        return f"{self.user.get_username()} — {escopo}"

    @property
    def is_geral(self):
        return self.user.is_superuser or self.congregation_id is None


CARGO_CHOICES = [
    ("membro", "Membro"),
    ("cooperador", "Cooperador"),
    ("diacono", "Diácono"),
    ("presbitero", "Presbítero"),
    ("evangelista", "Evangelista"),
    ("pastor", "Pastor"),
]


class Member(models.Model):
    congregation = models.ForeignKey(
        Congregation, on_delete=models.PROTECT, related_name="members", verbose_name="Congregação"
    )
    full_name = models.CharField("Nome completo", max_length=200)
    birth_date = models.DateField("Data de nascimento", null=True, blank=True)
    cargo = models.CharField("Cargo", max_length=20, choices=CARGO_CHOICES, default="membro")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        verbose_name = "Membro"
        verbose_name_plural = "Membros"
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name


class Minute(models.Model):
    congregation = models.ForeignKey(
        Congregation,
        on_delete=models.PROTECT,
        related_name="minutes",
        verbose_name="Congregação",
        null=True,
        blank=True,
        help_text="Deixe em branco para uma ata geral do Setor 46 (todas as congregações).",
    )
    title = models.CharField("Título", max_length=200)
    meeting_date = models.DateField("Data da reunião")
    file = models.FileField(
        "Arquivo (PDF)",
        upload_to="atas/%Y/%m/",
        null=True,
        blank=True,
        validators=[FileExtensionValidator(["pdf"])],
    )
    notes = models.TextField("Anotações / resumo", blank=True)
    published = models.BooleanField("Publicada no site público", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Ata de reunião"
        verbose_name_plural = "Atas de reuniões"
        ordering = ["-meeting_date"]

    def __str__(self):
        return f"{self.title} ({self.meeting_date:%d/%m/%Y})"


class Event(models.Model):
    congregation = models.ForeignKey(
        Congregation,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="Congregação",
        null=True,
        blank=True,
        help_text="Deixe em branco para um evento geral do Setor 46 (todas as congregações).",
    )
    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descrição", blank=True)
    event_date = models.DateTimeField("Data e hora")
    location = models.CharField("Local", max_length=250, blank=True)
    image = models.ImageField("Imagem do evento", upload_to="eventos/%Y/%m/", null=True, blank=True)
    published = models.BooleanField("Publicado no site público", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-event_date"]

    def __str__(self):
        return self.title


class Mensalidade(models.Model):
    congregation = models.ForeignKey(
        Congregation, on_delete=models.PROTECT, related_name="mensalidades", verbose_name="Congregação"
    )
    mes_referencia = models.DateField(
        "Mês de referência",
        help_text="Escolha qualquer dia do mês a que a mensalidade se refere (ex: 01/09/2026 para setembro/2026).",
    )
    valor = models.DecimalField("Valor pago", max_digits=8, decimal_places=2, null=True, blank=True)
    data_pagamento = models.DateField("Data do Pix", null=True, blank=True)
    comprovante = models.FileField(
        "Comprovante",
        upload_to="comprovantes/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
        help_text="PDF ou foto (JPG/PNG) do comprovante do Pix.",
        blank=True,
    )
    observacoes = models.TextField("Observações", blank=True)

    marcado_atrasado = models.BooleanField(
        "Marcar como atrasado",
        default=False,
        help_text="Só o administrador geral vê este campo — força este mês a aparecer como atrasado "
        "mesmo antes de o mês terminar (ex: a congregação já passou do prazo interno combinado).",
    )

    confirmado = models.BooleanField("Confirmado pelo administrador geral", default=False)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Confirmado por",
    )
    confirmado_em = models.DateTimeField("Confirmado em", null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField("Enviado em", auto_now_add=True)

    class Meta:
        verbose_name = "Mensalidade"
        verbose_name_plural = "Mensalidades"
        ordering = ["-mes_referencia", "congregation__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["congregation", "mes_referencia"], name="unica_mensalidade_por_congregacao_mes"
            )
        ]

    def save(self, *args, **kwargs):
        # Normaliza sempre para o dia 1, senão a mesma congregação poderia
        # enviar duas mensalidades para o mesmo mês só escolhendo dias
        # diferentes no calendário (a restrição unique_together comparia
        # datas exatas, não "mês e ano").
        if self.mes_referencia:
            self.mes_referencia = self.mes_referencia.replace(day=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.congregation.name} — {self.mes_referencia:%m/%Y}"
