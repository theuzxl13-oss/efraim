from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


GROUP_NAME = "Admin de Congregação"
ACOES = ["add", "change", "delete", "view"]


def restringir_grupo(apps, schema_editor):
    # Garante que as permissões padrão já existem antes de mexer nelas
    # (mesmo cuidado de timing da migração 0002).
    core_config = global_apps.get_app_config("core")
    create_permissions(core_config, apps=global_apps, verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Member = apps.get_model("core", "Member")

    group, _ = Group.objects.get_or_create(name=GROUP_NAME)

    ct = ContentType.objects.get_for_model(Member)
    perms = [
        Permission.objects.get(content_type=ct, codename=f"{acao}_member") for acao in ACOES
    ]
    # Administrador de congregação agora só gerencia Membros da própria
    # congregação; Atas e Eventos (inclusive publicação no site) passam a
    # ser exclusivos do administrador geral.
    group.permissions.set(perms)


def reverter(apps, schema_editor):
    # Não há como restaurar o estado anterior com segurança; mantém como está.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_minute_file"),
    ]

    operations = [
        migrations.RunPython(restringir_grupo, reverter),
    ]
