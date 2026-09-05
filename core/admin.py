from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from .models import AdminProfile, Congregation, Event, Member, Mensalidade, Minute


def add_months(data, n):
    """Soma (ou subtrai) n meses a uma data, sempre voltando ao dia 1."""
    mes_zero_indexado = data.month - 1 + n
    ano = data.year + mes_zero_indexado // 12
    mes = mes_zero_indexado % 12 + 1
    return data.replace(year=ano, month=mes, day=1)


def get_profile(request):
    return getattr(request.user, "admin_profile", None)


def is_geral(request):
    # Superusuário sempre tem acesso geral. Fora isso, só é "geral" quem tem um
    # perfil de administrador explícito com congregação em branco — um usuário
    # sem perfil nenhum (configuração incompleta) NÃO deve ganhar acesso total
    # por padrão, então aqui o comportamento é "fail closed".
    if request.user.is_superuser:
        return True
    profile = get_profile(request)
    return bool(profile) and profile.congregation_id is None


def my_congregation_id(request):
    profile = get_profile(request)
    return profile.congregation_id if profile else None


class EfraimAdminSite(admin.AdminSite):
    site_header = "Varões Efraim — Setor 46"
    site_title = "Painel Administrativo"
    index_title = "Painel de controle"

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        if request.user.is_authenticated:
            geral = is_geral(request)
            if geral:
                stats = Congregation.objects.annotate(total_membros=Count("members")).order_by("name")
                total_geral = Member.objects.count()
            else:
                cid = my_congregation_id(request)
                stats = Congregation.objects.filter(pk=cid).annotate(total_membros=Count("members"))
                total_geral = None
            extra_context["congregation_stats"] = stats
            extra_context["total_geral"] = total_geral
            extra_context["is_geral_admin"] = geral

            mes_atual = timezone.localdate().replace(day=1)
            pagas_ids = set(
                Mensalidade.objects.filter(mes_referencia=mes_atual, confirmado=True).values_list(
                    "congregation_id", flat=True
                )
            )
            if geral:
                extra_context["mensalidade_status"] = [
                    {"nome": c.name, "pago": c.id in pagas_ids} for c in stats
                ]
            else:
                extra_context["mensalidade_paga_este_mes"] = my_congregation_id(request) in pagas_ids
            extra_context["mensalidade_mes_atual"] = mes_atual
        return super().index(request, extra_context)

    def get_urls(self):
        urls = [
            path(
                "mensalidades/situacao/",
                self.admin_view(self.mensalidades_situacao_view),
                name="mensalidades_situacao",
            ),
        ]
        return urls + super().get_urls()

    def mensalidades_situacao_view(self, request):
        geral = is_geral(request)
        if geral:
            congregacoes = list(Congregation.objects.order_by("name"))
        else:
            congregacoes = list(Congregation.objects.filter(pk=my_congregation_id(request)))

        hoje = timezone.localdate().replace(day=1)
        ano_param = request.GET.get("ano")
        ano_selecionado = int(ano_param) if ano_param and ano_param.isdigit() else hoje.year

        inicio = hoje.replace(year=ano_selecionado, month=1, day=1)
        fim = hoje.replace(year=ano_selecionado, month=12, day=1)

        qs_congregacoes = Mensalidade.objects.filter(congregation__in=congregacoes)

        # No ano atual (visão padrão), estica a tabela automaticamente se
        # houver algum atraso mais antigo ou adiantamento mais à frente do
        # que o próprio ano — assim nada fica escondido sem querer. Ao
        # navegar para outro ano especificamente, mostra só aquele ano.
        if ano_selecionado == hoje.year:
            mais_antiga = (
                qs_congregacoes.order_by("mes_referencia").values_list("mes_referencia", flat=True).first()
            )
            mais_recente = (
                qs_congregacoes.order_by("-mes_referencia").values_list("mes_referencia", flat=True).first()
            )
            if mais_antiga and mais_antiga < inicio:
                inicio = mais_antiga.replace(day=1)
            if mais_recente and mais_recente > fim:
                fim = mais_recente.replace(day=1)

        meses = []
        m = inicio
        while m <= fim:
            meses.append(m)
            m = add_months(m, 1)

        registros = {(r.congregation_id, r.mes_referencia): r for r in qs_congregacoes}

        linhas = []
        for c in congregacoes:
            mes_criacao = timezone.localtime(c.created_at).date().replace(day=1)
            celulas = []
            for m in meses:
                registro = registros.get((c.id, m))
                if registro:
                    # Havendo registro, o status real dele sempre prevalece
                    # — mesmo que caia antes da data de criação "oficial" da
                    # congregação no sistema.
                    status = "pago" if registro.confirmado else "enviado"
                elif m < mes_criacao:
                    # Sem registro e a congregação ainda não existia nesse
                    # mês — não faz sentido cobrar mensalidade de um mês
                    # antes dela ser cadastrada no sistema.
                    status = "futuro"
                elif m < hoje:
                    status = "atrasado"
                elif m == hoje:
                    status = "pendente"
                else:
                    status = "futuro"
                celulas.append({"mes": m, "status": status, "registro": registro})
            linhas.append({"congregation": c, "celulas": celulas})

        context = {
            **self.each_context(request),
            "title": "Situação das mensalidades",
            "ano_selecionado": ano_selecionado,
            "ano_anterior": ano_selecionado - 1,
            "ano_seguinte": ano_selecionado + 1,
            "meses": meses,
            "linhas": linhas,
            "is_geral_admin": geral,
        }
        return TemplateResponse(request, "admin/mensalidades_situacao.html", context)


site = EfraimAdminSite(name="efraim_admin")


class CongregationScopedAdmin(admin.ModelAdmin):
    """Base para modelos ligados a uma congregação: restringe visão e edição
    ao escopo do administrador logado (geral vê tudo, congregação vê só a sua)."""

    congregation_field = "congregation"
    exclude = ("created_by",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if is_geral(request):
            return qs
        return qs.filter(**{self.congregation_field: my_congregation_id(request)})

    def save_model(self, request, obj, form, change):
        if not is_geral(request):
            setattr(obj, self.congregation_field, Congregation.objects.get(pk=my_congregation_id(request)))
        if hasattr(obj, "created_by_id") and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == self.congregation_field and not is_geral(request):
            cid = my_congregation_id(request)
            kwargs["queryset"] = Congregation.objects.filter(pk=cid)
            kwargs["initial"] = cid
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if obj is not None and not is_geral(request):
            if getattr(obj, f"{self.congregation_field}_id") != my_congregation_id(request):
                return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not is_geral(request):
            if getattr(obj, f"{self.congregation_field}_id") != my_congregation_id(request):
                return False
        return super().has_delete_permission(request, obj)


class GeralOnlyAdmin(admin.ModelAdmin):
    """Base para modelos visíveis/editáveis só por administradores gerais
    (Congregações, Usuários, Atas e Eventos) — administradores de congregação
    não acessam nada aqui."""

    exclude = ("created_by",)

    def _allowed(self, request):
        return bool(request.user.is_active and request.user.is_staff and is_geral(request))

    def save_model(self, request, obj, form, change):
        if hasattr(obj, "created_by_id") and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def has_module_permission(self, request):
        return self._allowed(request)

    def has_view_permission(self, request, obj=None):
        return self._allowed(request)

    def has_add_permission(self, request):
        return self._allowed(request)

    def has_change_permission(self, request, obj=None):
        return self._allowed(request)

    def has_delete_permission(self, request, obj=None):
        return self._allowed(request)


@admin.register(Congregation, site=site)
class CongregationAdmin(GeralOnlyAdmin):
    list_display = ("name", "total_membros", "created_at")
    search_fields = ("name",)

    def total_membros(self, obj):
        return obj.members.count()

    total_membros.short_description = "Total de membros"


@admin.register(Member, site=site)
class MemberAdmin(CongregationScopedAdmin):
    list_display = ("full_name", "congregation", "cargo", "birth_date")
    list_filter = ("congregation", "cargo")
    search_fields = ("full_name",)


@admin.register(Minute, site=site)
class MinuteAdmin(GeralOnlyAdmin):
    list_display = ("title", "congregation", "meeting_date", "published")
    list_filter = ("congregation", "published")
    search_fields = ("title", "notes")
    date_hierarchy = "meeting_date"


@admin.register(Mensalidade, site=site)
class MensalidadeAdmin(CongregationScopedAdmin):
    list_display = ("congregation", "mes_referencia", "valor", "data_pagamento", "confirmado")
    list_filter = ("congregation", "confirmado")
    search_fields = ("congregation__name",)
    date_hierarchy = "mes_referencia"
    actions = ["marcar_confirmado"]

    def get_exclude(self, request, obj=None):
        campos = list(super().get_exclude(request, obj) or [])
        if not is_geral(request):
            campos += ["confirmado", "confirmado_por", "confirmado_em"]
        return campos

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Admin de congregação precisa sempre anexar o comprovante; admin
        # geral pode confirmar/cadastrar direto, sem exigir arquivo.
        if "comprovante" in form.base_fields:
            form.base_fields["comprovante"].required = not is_geral(request)
        return form

    def has_change_permission(self, request, obj=None):
        if obj is not None and not is_geral(request) and obj.confirmado:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and not is_geral(request) and obj.confirmado:
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not is_geral(request):
            actions.pop("marcar_confirmado", None)
        return actions

    @admin.action(description="Marcar selecionadas como confirmadas (pagas)")
    def marcar_confirmado(self, request, queryset):
        queryset.update(confirmado=True, confirmado_por=request.user, confirmado_em=timezone.now())


@admin.register(Event, site=site)
class EventAdmin(GeralOnlyAdmin):
    list_display = ("title", "congregation", "event_date", "location", "published")
    list_filter = ("congregation", "published")
    search_fields = ("title", "description", "location")
    date_hierarchy = "event_date"


class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    fk_name = "user"
    extra = 1
    max_num = 1
    verbose_name = "Escopo de acesso"
    verbose_name_plural = "Escopo de acesso"


@admin.register(User, site=site)
class UserAdmin(GeralOnlyAdmin, DjangoUserAdmin):
    inlines = [AdminProfileInline]
    list_display = ("username", "get_full_name", "is_staff", "is_superuser", "escopo")

    def escopo(self, obj):
        profile = getattr(obj, "admin_profile", None)
        if obj.is_superuser or not (profile and profile.congregation_id):
            return "Geral (todas as congregações)"
        return profile.congregation.name

    escopo.short_description = "Acesso"
