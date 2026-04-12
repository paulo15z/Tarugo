# Generated migration for adding ambiente details fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comercial', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ambienteoramento',
            name='acabamentos',
            field=models.JSONField(blank=True, default=list, help_text='Lista de acabamentos (materiais, cores, dimensões, etc)', verbose_name='Acabamentos'),
        ),
        migrations.AddField(
            model_name='ambienteoramento',
            name='eletrodomesticos',
            field=models.JSONField(blank=True, default=list, help_text='Lista de eletrodomésticos (marca, modelo, capacidade)', verbose_name='Eletrodomésticos'),
        ),
        migrations.AddField(
            model_name='ambienteoramento',
            name='observacoes_especiais',
            field=models.TextField(blank=True, default='', help_text='Itens que precisam atenção especial na Engenharia', verbose_name='Observações especiais'),
        ),
    ]

