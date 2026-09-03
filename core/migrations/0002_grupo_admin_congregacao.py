from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations


GROUP_NAME = "Admin de Congregação"
MODELOS = ["member", "minute", "event"]
ACOES = ["add", "change", "delete", "view"]


def criar_grupo(apps, schema_editor):
    # As permissões padrão (add/change/delete/view) só são criadas pelo Django
    # através do sinal post_migrate, que dispara depois que TODAS as migrações
    # da execução atual terminam — ou seja, ainda não existem neste ponto.
    # Precisamos criá-las manualmente aqui antes de atribuí-las ao grupo.
    core_config = global_apps.get_app_config("core")
    create_permissions(core_config, apps=global_apps, verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    group, _ = Group.objects.get_or_create(name=GROUP_NAME)

    Member = apps.get_model("core", "Member")
    Minute = apps.get_model("core", "Minute")
    Event = apps.get_model("core", "Event")
    modelo_por_nome = {"member": Member, "minute": Minute, "event": Event}

    perms = []
    for nome_modelo in MODELOS:
        ct = ContentType.objects.get_for_model(modelo_por_nome[nome_modelo])
        for acao in ACOES:
            codename = f"{acao}_{nome_modelo}"
            try:
                perms.append(Permission.objects.get(content_type=ct, codename=codename))
            except Permission.DoesNotExist:
                pass
    group.permissions.set(perms)


def remover_grupo(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name=GROUP_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("auth", "__latest__"),
    ]

    operations = [
        migrations.RunPython(criar_grupo, remover_grupo),
    ]
