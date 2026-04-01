# apps/estoque/management/commands/seed_categorias.py
from django.core.management.base import BaseCommand
from apps.estoque.models.categoria import CategoriaProduto


class Command(BaseCommand):
    help = "Popula categorias otimizadas para indústria moveleira (Tarugo)"

    def handle(self, *args, **options):
        self.stdout.write("🌳 Iniciando seed de categorias...")

        # Categorias raiz
        raizes = ["Matéria-Prima", "Ferragens", "Fitas de Borda", "Elétrica", "Suprimentos"]
        for i, nome in enumerate(raizes):
            CategoriaProduto.objects.get_or_create(
                nome=nome, 
                parent=None, 
                defaults={"ordem": i}
            )

        # Subcategorias
        subcategorias = {
            "Matéria-Prima": ["MDF", "Compensado", "Outras Chapas"],
            "Ferragens": [
                "Dobradiças", 
                "Corrediças", 
                "Trilhos",
                "Kits Deslizantes",
                "Sistemas de Abertura",
                "Puxadores e Botões",
                "Parafusos e Fixadores",
                "Dispositivos de Montagem",
                "Outras Ferragens",
            ],
            "Suprimentos": ["Embalagens e Proteção", "Químicos e Insumos", "Outros Suprimentos"],
        }

        criados = 0
        for parent_nome, subs in subcategorias.items():
            parent = CategoriaProduto.objects.filter(nome=parent_nome, parent=None).first()
            if not parent:
                continue

            for sub_nome in subs:
                obj, created = CategoriaProduto.objects.get_or_create(
                    nome=sub_nome,
                    parent=parent,
                    defaults={"ordem": subs.index(sub_nome)}
                )
                if created:
                    criados += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ {parent.nome} → {sub_nome}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Seed finalizado! {criados} subcategorias criadas."))