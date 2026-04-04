import os
import django
import sys

# Setup Django environment
sys.path.append('/home/ubuntu/Tarugo')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
# Adiciona o diretório atual ao path para encontrar os apps
sys.path.append(os.getcwd())
django.setup()

from apps.estoque.models import Produto, CategoriaProduto, SaldoMDF
from apps.estoque.services.produto_service import ProdutoService

def run():
    mdf_finishes = [
        ("Bruma", "Flora", "Instantes da Floresta (2026)"),
        ("Alvorecer", "Flora", "Instantes da Floresta (2026)"),
        ("Tauari Zênite", "Flora", "Instantes da Floresta (2026)"),
        ("Jequitibá Poente", "Flora", "Instantes da Floresta (2026)"),
        ("Freijó Puro", "Duratex", "Essencial Wood"),
        ("Carvalho Brizza", "Duratex", "Essencial Wood"),
        ("Azul Marinho", "Guararapes", "Áris (Superfosco)"),
        ("Ametista", "Guararapes", "Áris (Superfosco)"),
        ("Nogueira Âmbar", "Guararapes", "Madeiras do Mundo"),
        ("Carvalho Capri", "Guararapes", "Madeiras do Mundo"),
        ("Metal Champagne", "Guararapes", "Metalizados"),
        ("Cinza Sagrado", "Arauco", "Matt"),
        ("Verde Jade", "Arauco", "Matt"),
        ("Terracotta", "Arauco", "Matt"),
        ("Noce Oro", "Arauco", "Woods"),
        ("Carbono", "Duratex", "Velluto"),
        ("Gianduia", "Duratex", "Cristallo (Alto Brilho)"),
        ("Titanio", "Duratex", "Cristallo (Alto Brilho)"),
        ("Carvalho Malva", "Duratex", "Essencial Wood"),
        ("Alecrim", "Duratex", "Velluto"),
        ("Moss", "Duratex", "Velluto"),
        ("Gaia", "Duratex", "Design"),
        ("Fresno Açores", "Guararapes", "Syncro Ash"),
        ("Fresno Aveiro", "Guararapes", "Syncro Ash"),
        ("Salerno", "Guararapes", "Madeiras do Mundo"),
        ("Nogueira Rubi", "Guararapes", "Madeiras do Mundo"),
        ("Pau-Ferro", "Guararapes", "Dual Syncro"),
        ("Savana", "Guararapes", "Dual Syncro"),
        ("Nude", "Arauco", "Matt"),
        ("Louro Freijó", "Arauco", "Woods"),
        ("Carvalho Treviso", "Arauco", "Woods"),
        ("Cumaru", "Arauco", "Woods"),
        ("Jequitibá", "Arauco", "Woods"),
        ("Grafite", "Arauco", "Matt"),
        ("Branco Diamante", "Duratex", "Essencial"),
        ("Preto", "Duratex", "Essencial"),
        ("Ocre", "Duratex", "Velluto"),
        ("Crepúsculo", "Flora", "Instantes da Floresta (2026)"),
        ("Carvalho Amanhecer", "Flora", "Instantes da Floresta (2026)"),
        ("Arpoador", "Sudati", "Madeirados"),
        ("Itaparica", "Sudati", "Madeirados"),
        ("Jalapão", "Sudati", "Madeirados"),
        ("Canário", "Sudati", "Cores"),
        ("Arenas", "Eucatex", "Matt Soft"),
        ("Cinnamon", "Eucatex", "Matt Soft"),
        ("Verde Eucalipto", "Eucatex", "Matt Soft"),
        ("Mineral", "Eucatex", "Lacca AD"),
        ("Argento", "Eucatex", "Lacca AD"),
        ("Carvalho Hanover", "Eucatex", "Wood"),
        ("Nogueira Flórida", "Duratex", "Design"),
    ]

    try:
        mdf_category = CategoriaProduto.objects.get(nome="MDF")
    except CategoriaProduto.DoesNotExist:
        print("Erro: Categoria 'MDF' não encontrada. Execute o seed primeiro.")
        return

    print(f"🌳 Iniciando inserção de {len(mdf_finishes)} acabamentos de MDF...")
    
    for i, (nome, fabricante, linha) in enumerate(mdf_finishes, 1):
        sku = f"MDF-{fabricante[:3].upper()}-{nome[:3].upper()}-{i:02d}"
        
        data = {
            'nome': f"MDF {nome}",
            'sku': sku,
            'categoria_id': mdf_category.id,
            'unidade_medida': 'm2',
            'estoque_minimo': 0,
            'atributos_especificos': {
                'fabricante': fabricante,
                'linha': linha,
                'acabamento': nome
            }
        }
        
        try:
            # Check if product already exists
            produto = Produto.objects.filter(sku=sku).first()
            if produto:
                print(f"⚠️ {i:02d}/50: {nome} ({fabricante}) - SKU {sku} já existe. Inicializando espessuras...")
                # Inicializa espessuras padrão se for MDF
                espessuras_padrao = [6, 15, 18, 25]
                for esp in espessuras_padrao:
                    SaldoMDF.objects.get_or_create(
                        produto=produto,
                        espessura=esp,
                        defaults={'quantidade': 0}
                    )
                continue
                
            ProdutoService.criar_produto(data)
            print(f"✅ {i:02d}/50: {nome} ({fabricante}) cadastrado com sucesso!")
        except Exception as e:
            print(f"❌ {i:02d}/50: Erro ao cadastrar {nome}: {str(e)}")

    print("\n🚀 Processo concluído!")

if __name__ == "__main__":
    run()
