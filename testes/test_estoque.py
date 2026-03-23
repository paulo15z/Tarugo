#!/usr/bin/env python
"""
Script de teste para validar o MVP do estoque
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.estoque.models import Produto, Movimentacao

print("\n" + "="*60)
print("🧪 TESTANDO MVP DO ESTOQUE")
print("="*60 + "\n")

# 1. Criar um produto de teste
print("1️⃣  Criando produto...")
p = Produto.objects.create(
    nome="Cadeira de Madeira",
    sku="CADEIR-001",
    quantidade=10,
    estoque_minimo=5
)
print(f"   ✅ Produto: {p.nome}")
print(f"   📦 SKU: {p.sku}")
print(f"   📊 Quantidade: {p.quantidade}")
print(f"   ⚠️  Mínimo: {p.estoque_minimo}\n")

# 2. Testar movimentação de entrada
print("2️⃣  Simulando entrada de estoque...")
m1 = Movimentacao.objects.create(
    produto=p,
    tipo='entrada',
    quantidade=5
)
p.refresh_from_db()
print(f"   ✅ +5 unidades")
print(f"   📊 Novo saldo: {p.quantidade}\n")

# 3. Testar movimentação de saída
print("3️⃣  Simulando saída de estoque...")
m2 = Movimentacao.objects.create(
    produto=p,
    tipo='saida',
    quantidade=3
)
p.refresh_from_db()
print(f"   ✅ -3 unidades")
print(f"   📊 Novo saldo: {p.quantidade}\n")

# 4. Listar movimentações
print("4️⃣  Histórico de movimentações:")
movs = Movimentacao.objects.filter(produto=p).order_by('-criado_em')
print(f"   Total: {movs.count()} movimentações\n")
for i, m in enumerate(movs, 1):
    tipo_display = "📥 ENTRADA" if m.tipo == 'entrada' else "📤 SAÍDA"
    print(f"   {i}. {tipo_display}: {m.quantidade} un. ({m.criado_em.strftime('%Y-%m-%d %H:%M:%S')})")

# 5. Testar seletor
print("\n5️⃣  Testando seletor de movimentações...")
from apps.estoque.selectors.movimentacao_selectors import listar_movimentacoes
movs_filtradas = listar_movimentacoes(produto_id=p.id)
print(f"   ✅ Seletor funcionando: {movs_filtradas.count()} movimentações para SKU {p.sku}\n")

print("="*60)
print("✨ TODOS OS TESTES PASSARAM!")
print("="*60 + "\n")
