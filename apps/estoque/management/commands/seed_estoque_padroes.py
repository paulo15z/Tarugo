from django.core.management.base import BaseCommand
from apps.estoque.models.categoria import CategoriaProduto
from apps.estoque.models.produto import Produto
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Injeta padrões de mercado (Duratex, Arauco, Leo) nas espessuras 6, 15, 18 e 25mm'

    def handle(self, *args, **options):
        # 1. Garantir Categorias Base
        cat_materia_prima, _ = CategoriaProduto.objects.get_or_create(nome="Matéria-Prima")
        cat_mdf, _ = CategoriaProduto.objects.get_or_create(nome="MDF", parent=cat_materia_prima)

        marcas = {
            "Duratex": ["Branco Diamante", "Carvalho Malva", "Gianduia", "Preto Silk"],
            "Arauco": ["Branco Supremo", "Noce Oro", "Grafite", "Louro Freijó"],
            "Leo Madeiras": ["Branco TX", "Nogueira Sevilha", "Cinza Sagrado"]
        }

        espessuras = [6, 15, 18, 25]
        count = 0

        for marca, padroes in marcas.items():
            for padrao in padroes:
                for esp in espessuras:
                    nome_completo = f"MDF {esp}mm {marca} {padrao}"
                    sku = slugify(f"{marca}-{padrao}-{esp}mm").upper()
                    
                    produto, criado = Produto.objects.get_or_create(
                        sku=sku,
                        defaults={
                            'nome': nome_completo,
                            'categoria': cat_mdf,
                            'unidade_medida': 'm2',
                            'quantidade': 50, # Estoque inicial para testes
                            'estoque_minimo': 10,
                            'atributos_especificos': {
                                'marca': marca,
                                'padrao': padrao,
                                'espessura': esp
                            }
                        }
                    )
                    if criado:
                        count += 1

        self.stdout.write(self.style.SUCCESS(f'Sucesso! {count} novos produtos injetados no estoque.'))
