#!/usr/bin/env python3
"""
VALIDAÇÃO DE SCHEMAS DINABOX

Script para validar os 3 schemas contra response3.json.
Roda: python test_schemas.py
"""

import json
from pathlib import Path
import sys

# Adicionar diretório do projeto ao path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from apps.integracoes.dinabox.schemas.router import DinaboxRouter


def test_response_sample():
    """Testa os 3 schemas contra response3.json real."""
    
    # Carregar response3.json
    response_path = project_root / "dinabox samples" / "response3.json"
    
    if not response_path.exists():
        print(f"❌ Arquivo não encontrado: {response_path}")
        return False
    
    print(f"📂 Carregando: {response_path}")
    
    with open(response_path, "r", encoding="utf-8") as f:
        raw_json = json.load(f)
    
    print(f"✅ JSON carregado ({len(json.dumps(raw_json))} bytes)\n")
    
    # Inicializar router
    router = DinaboxRouter(raw_json)
    
    # Validar todos
    print("🔍 Validando schemas...")
    success = router.validate_all()
    
    if not success:
        print("\n❌ Erros de validação encontrados:")
        for error in router.errors:
            print(f"  - {error}")
        return False
    
    print("✅ Todos os schemas são válidos!\n")
    
    # Testar administrativo
    print("📊 ADMINISTRATIVO (PCP/Financeiro):")
    try:
        admin = router.administrativo()
        print(f"  - Projeto: {admin.project_id} - {admin.project_description}")
        print(f"  - Módulos: {admin.total_modules}")
        print(f"  - Peças: {admin.total_parts}")
        print(f"  - Insumos: {admin.total_inputs}")
        print(f"  - Custo total: R$ {admin.total_materials_cost:.2f}")
        bom = admin.get_bom_summary()
        print(f"  - Materiais únicos: {len(bom['materials'])}")
        print(f"  - Itens de hardware: {len(bom['hardware'])}")
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False
    
    print()
    
    # Testar operacional
    print("🏭 OPERACIONAL (Bipagem/Fábrica):")
    try:
        ops = router.operacional()
        print(f"  - Projeto: {ops.project_id}")
        print(f"  - Módulos: {ops.total_modules}")
        print(f"  - Peças: {ops.total_parts}")
        print(f"  - Operações de usinagem: {ops.total_holes}")
        print(f"  - Rebordos a processar: {ops.total_edges_to_band}")
        summary = ops.get_manufacturing_summary()
        print(f"  - Módulos com detalhes:")
        for mod in summary["modules"]:
            print(f"    • {mod['name']}: {mod['parts']} peças, {mod['holes']} furos, {mod['edges']} rebordos")
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False
    
    print()
    
    # Testar logístico
    print("📦 LOGÍSTICO (Expedição):")
    try:
        log = router.logistico()
        print(f"  - Projeto: {log.project_id}")
        print(f"  - Cliente: {log.customer.customer_name}")
        print(f"  - Endereço: {log.customer.customer_address}")
        print(f"  - Módulos para expedição: {log.total_modules}")
        print(f"  - Itens para conferência: {log.total_items}")
        print(f"  - Volume estimado: {log.total_volume_m3:.2f} m³")
        shipment = log.get_shipment_summary()
        print(f"  - Itens no resumo: {len(shipment['items_detail'])}")
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False
    
    print("\n✅ Validação completa com sucesso!")
    return True


if __name__ == "__main__":
    success = test_response_sample()
    sys.exit(0 if success else 1)
