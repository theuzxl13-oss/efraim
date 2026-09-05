from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


GROUP_NAME = "Admin de Congregação"
ACOES = ["add", "change", "delete", "view"]


def adicionar_permissao_mensalidade(apps, schema_editor):
    core_config = global_apps.get_app_config("core")
    create_permissions(core_config, apps=global_apps, verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Mensalidade = apps.get_model("core", "Mensalidade")

    group, _ = Group.objects.get_or_create(name=GROUP_NAME)
    ct = ContentType.objects.get_for_model(Mensalidade)
    perms = [Permission.objects.get(content_type=ct, codename=f"{acao}_mensalidade") for acao in ACOES]
    for p in perms:
        group.permissions.add(p)


def remover_permissao_mensalidade(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")
    Mensalidade = apps.get_model("core", "Mensalidade")

    try:
        group = Group.objects.get(name=GROUP_NAME)
    except Group.DoesNotExist:
        return
    ct = ContentType.objects.get_for_model(Mensalidade)
    perms = Permission.objects.filter(content_type=ct)
    group.permissions.remove(*perms)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_mensalidade"),
    ]

    operations = [
        migrations.RunPython(adicionar_permissao_mensalidade, remover_permissao_mensalidade),
    ]
