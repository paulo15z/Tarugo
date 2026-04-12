# Generated manually — grupos Django para o setor Comercial.

from django.db import migrations


def forwards(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    ct_ids = list(
        ContentType.objects.filter(
            app_label="comercial",
            model__in=["clientecomercial", "observacaocomercial", "ambienteoramento"],
        ).values_list("id", flat=True)
    )
    if len(ct_ids) != 3:
        return

    todas = list(Permission.objects.filter(content_type_id__in=ct_ids))
    somente_ver = [p for p in todas if p.codename.startswith("view_")]
    sem_del_cliente = [p for p in todas if p.codename != "delete_clientecomercial"]

    g_orc, _ = Group.objects.get_or_create(name="comercial_orcamentista")
    g_orc.permissions.set(todas)

    g_cons, _ = Group.objects.get_or_create(name="comercial_consultor")
    g_cons.permissions.set(sem_del_cliente)

    g_lei, _ = Group.objects.get_or_create(name="comercial_leitura")
    g_lei.permissions.set(somente_ver)


def backwards(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in ("comercial_orcamentista", "comercial_consultor", "comercial_leitura"):
        Group.objects.filter(name=name).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("comercial", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
