from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User
from django.db.models import Count

from .models import AdminProfile, Congregation, Event, Member, Minute


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
            if is_geral(request):
                stats = Congregation.objects.annotate(total_membros=Count("members")).order_by("name")
                total_geral = Member.objects.count()
            else:
                cid = my_congregation_id(request)
                stats = Congregation.objects.filter(pk=cid).annotate(total_membros=Count("members"))
                total_geral = None
            extra_context["congregation_stats"] = stats
            extra_context["total_geral"] = total_geral
            extra_context["is_geral_admin"] = is_geral(request)
        return super().index(request, extra_context)


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
    (Congregações e Usuários) — administradores de congregação não acessam."""

    def _allowed(self, request):
        return bool(request.user.is_active and request.user.is_staff and is_geral(request))

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
