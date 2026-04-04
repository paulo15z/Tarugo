# apps/estoque/management/commands/seed_categorias.py
from django.core.management.base import BaseCommand
from apps.estoque.models.categoria import CategoriaProduto
from apps.estoque.domain.tipos import FamiliaProduto


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

        # Subcategorias com Famílias
        subcategorias = {
            "Matéria-Prima": [
                ("MDF", FamiliaProduto.MDF),
                ("Compensado", FamiliaProduto.MDF),
                ("Outras Chapas", FamiliaProduto.MDF),
            ],
            "Ferragens": [
                ("Dobradiças", FamiliaProduto.FERRAGENS),
                ("Corrediças", FamiliaProduto.FERRAGENS),
                ("Trilhos", FamiliaProduto.FERRAGENS),
                ("Kits Deslizantes", FamiliaProduto.FERRAGENS),
                ("Sistemas de Abertura", FamiliaProduto.FERRAGENS),
                ("Puxadores e Botões", FamiliaProduto.FERRAGENS),
                ("Parafusos e Fixadores", FamiliaProduto.FERRAGENS),
                ("Dispositivos de Montagem", FamiliaProduto.FERRAGENS),
                ("Outras Ferragens", FamiliaProduto.FERRAGENS),
            ],
            "Fitas de Borda": [
                ("PVC", FamiliaProduto.FITAS_BORDA),
                ("ABS", FamiliaProduto.FITAS_BORDA),
                ("Madeira Natural", FamiliaProduto.FITAS_BORDA),
            ],
            "Suprimentos": [
                ("Embalagens e Proteção", FamiliaProduto.EMBALAGENS),
                ("Químicos e Insumos", FamiliaProduto.QUIMICOS_INSUMOS),
                ("EPIs e Ferramentas", FamiliaProduto.EPIS_FERRAMENTAS),
                ("Outros Suprimentos", FamiliaProduto.OUTROS),
            ],
            "Vidros e Espelhos": [
                ("Vidros", FamiliaProduto.VIDROS_ESPELHOS),
                ("Espelhos", FamiliaProduto.VIDROS_ESPELHOS),
            ]
        }

        criados = 0
        for parent_nome, subs in subcategorias.items():
            parent, _ = CategoriaProduto.objects.get_or_create(nome=parent_nome, parent=None)
            
            for i, (sub_nome, familia) in enumerate(subs):
                obj, created = CategoriaProduto.objects.update_or_create(
                    nome=sub_nome,
                    parent=parent,
                    defaults={
                        "ordem": i,
                        "familia": familia
                    }
                )
                if created:
                    criados += 1
                    self.stdout.write(self.style.SUCCESS(f"✓ {parent.nome} → {sub_nome}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Seed finalizado! {criados} subcategorias criadas."))