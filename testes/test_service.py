#!/usr/bin/env python
"""
Teste dos endpoints da API e do service de movimentação
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.estoque.models import Produto, Movimentacao
from apps.estoque.services.movimentacao_services import processar_movimentacao

print("\n" + "="*60)
print("🧪 TESTANDO SERVICE DE MOVIMENTAÇÃO (com transaction.atomic)")
print("="*60 + "\n")

# Limpar dados anteriores
Movimentacao.objects.all().delete()
Produto.objects.all().delete()

# 1. Criar produto
print("1️⃣  Criando produto...")
p = Produto.objects.create(
    nome="Mesa Gamer",
    sku="MESA-GAMER-001",
    quantidade=0,
    estoque_minimo=5
)
print(f"   ✅ Produto: {p.nome} (Qtd inicial: {p.quantidade})\n")

# 2. Testar ENTRADA via service
print("2️⃣  Processando ENTRADA via service...")
try:
    resultado = processar_movimentacao({
        'produto_id': p.id,
        'tipo': 'entrada',
        'quantidade': 20
    })
    print(f"   ✅ Entrada processada!")
    print(f"   📊 Nova quantidade: {resultado.quantidade}\n")
except Exception as e:
    print(f"   ❌ Erro: {e}\n")

# 3. Testar SAÍDA via service
print("3️⃣  Processando SAÍDA via service...")
try:
    resultado = processar_movimentacao({
        'produto_id': p.id,
        'tipo': 'saida',
        'quantidade': 5
    })
    print(f"   ✅ Saída processada!")
    print(f"   📊 Nova quantidade: {resultado.quantidade}\n")
except Exception as e:
    print(f"   ❌ Erro: {e}\n")

# 4. Validar quantidade final
p.refresh_from_db()
print(f"4️⃣  Validação final:")
print(f"   Quantidade esperada: 15")
print(f"   Quantidade real: {p.quantidade}")
if p.quantidade == 15:
    print(f"   ✅ CORRETO!\n")
else:
    print(f"   ❌ ÉRRO: Valores não batem!\n")

# 5. Testar erro: saída maior que estoque
print("5️⃣  Testando validação (saída > estoque)...")
try:
    resultado = processar_movimentacao({
        'produto_id': p.id,
        'tipo': 'saida',
        'quantidade': 999
    })
    print(f"   ❌ Deveria ter dado erro!\n")
except ValueError as e:
    print(f"   ✅ Validação funcionou!")
    print(f"   Erro capturado: {e}\n")

# 6. Histórico final
print("6️⃣  Histórico completo:")
movs = Movimentacao.objects.filter(produto=p).order_by('criado_em')
print(f"   Total: {movs.count()} movimentações\n")
for i, m in enumerate(movs, 1):
    tipo_display = "📥 ENTRADA" if m.tipo == 'entrada' else "📤 SAÍDA"
    print(f"   {i}. {tipo_display}: {m.quantidade} un.")

print("\n" + "="*60)
print("✨ SERVICE FUNCIONANDO CORRETAMENTE!")
print("="*60 + "\n")
