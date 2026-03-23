#!/usr/bin/env python
"""
Teste de paginação do histórico de movimentações
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.estoque.models import Produto, Movimentacao
from django.test import RequestFactory
from apps.estoque.api.views import MovimentacaoListView

print("\n" + "="*70)
print("🧪 TESTANDO PAGINAÇÃO DO HISTÓRICO")
print("="*70 + "\n")

# Limpar dados anteriores
Movimentacao.objects.all().delete()
Produto.objects.all().delete()

# 1. Criar produto
print("1️⃣  Criando produto...")
p = Produto.objects.create(
    nome="Sofá Cinzento",
    sku="SOFA-CINZA-001",
    quantidade=0,
    estoque_minimo=5
)
print(f"   ✅ Produto: {p.nome}\n")

# 2. Criar múltiplas movimentações (para testar paginação)
print("2️⃣  Criando 15 movimentações...")
for i in range(1, 16):
    tipo = 'entrada' if i % 2 == 0 else 'saida'
    Movimentacao.objects.create(
        produto=p,
        tipo=tipo,
        quantidade=i
    )
print(f"   ✅ 15 movimentações criadas\n")

# 3. Testar paginação via API
print("3️⃣  Testando endpoints de paginação...\n")

factory = RequestFactory()
view = MovimentacaoListView.as_view()

# Teste 1: Primeiros 5 registros
print("   📄 Teste 1: GET /movimentacoes/?limit=5&offset=0")
request = factory.get('/movimentacoes/?limit=5&offset=0')
response = view(request)
data = response.data

print(f"      - Total de registros: {data['meta']['total']}")
print(f"      - Retornados: {len(data['data'])}")
print(f"      - Tem próxima: {data['meta']['tem_proxima']}")
assert data['meta']['total'] == 15, "Total deve ser 15"
assert len(data['data']) == 5, "Deve retornar 5 registros"
assert data['meta']['tem_proxima'] == True, "Deve ter próxima página"
print(f"      ✅ PASSOU\n")

# Teste 2: Próximos 5 registros (offset=5)
print("   📄 Teste 2: GET /movimentacoes/?limit=5&offset=5")
request = factory.get('/movimentacoes/?limit=5&offset=5')
response = view(request)
data = response.data

print(f"      - Retornados: {len(data['data'])}")
print(f"      - Offset: {data['meta']['offset']}")
print(f"      - Tem próxima: {data['meta']['tem_proxima']}")
assert len(data['data']) == 5, "Deve retornar 5 registros"
assert data['meta']['offset'] == 5, "Offset deve ser 5"
assert data['meta']['tem_proxima'] == True, "Deve ter próxima página"
print(f"      ✅ PASSOU\n")

# Teste 3: Última página (offset=10, limit=5 → retorna 5, sem próxima)
print("   📄 Teste 3: GET /movimentacoes/?limit=5&offset=10")
request = factory.get('/movimentacoes/?limit=5&offset=10')
response = view(request)
data = response.data

print(f"      - Retornados: {len(data['data'])}")
print(f"      - Tem próxima: {data['meta']['tem_proxima']}")
assert len(data['data']) == 5, "Deve retornar 5 registros"
assert data['meta']['tem_proxima'] == False, "Não deve ter próxima página"
print(f"      ✅ PASSOU\n")

# Teste 4: Limite maior que total
print("   📄 Teste 4: GET /movimentacoes/?limit=100&offset=0")
request = factory.get('/movimentacoes/?limit=100&offset=0')
response = view(request)
data = response.data

print(f"      - Retornados: {len(data['data'])}")
print(f"      - Tem próxima: {data['meta']['tem_proxima']}")
assert len(data['data']) == 15, "Deve retornar todos os 15"
assert data['meta']['tem_proxima'] == False, "Não deve ter próxima página"
print(f"      ✅ PASSOU\n")

# Teste 5: Com filtro de produto + paginação
print("   📄 Teste 5: GET /movimentacoes/?produto_id=X&limit=3&offset=0")
request = factory.get(f'/movimentacoes/?produto_id={p.id}&limit=3&offset=0')
response = view(request)
data = response.data

print(f"      - Total: {data['meta']['total']}")
print(f"      - Retornados: {len(data['data'])}")
assert data['meta']['total'] == 15, "Deve ter 15 movimentações do produto"
assert len(data['data']) == 3, "Deve retornar 3 registros"
print(f"      ✅ PASSOU\n")

# Teste 6: Validação de erros (limit inválido)
print("   📄 Teste 6: GET /movimentacoes/?limit=abc (inválido)")
request = factory.get('/movimentacoes/?limit=abc')
response = view(request)

print(f"      - Status: {response.status_code}")
assert response.status_code == 400, "Deve retornar erro 400"
print(f"      - Erro: {response.data['error']}")
print(f"      ✅ PASSOU\n")

print("="*70)
print("✨ TODOS OS TESTES DE PAGINAÇÃO PASSARAM!")
print("="*70 + "\n")

print("📋 Exemplo de resposta com paginação:")
print(json.dumps({
    "meta": {
        "total": 15,
        "limit": 5,
        "offset": 0,
        "tem_proxima": True
    },
    "data": "[... movimentações ...]"
}, indent=2))
print()
