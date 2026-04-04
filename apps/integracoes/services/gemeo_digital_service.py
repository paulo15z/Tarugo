# apps/integracoes/services/gemeo_digital_service.py
from decimal import Decimal
from django.db import transaction
from apps.bipagem.models.peca import Peca
from apps.integracoes.models import MapeamentoMaterial
from apps.estoque.services.movimentacao_service import MovimentacaoService

class GemeoDigitalService:
    """
    Coração da sincronização entre o Digital e o Físico.
    Garante que cada ação na produção (bipagem) reflita no estoque.
    """

    @staticmethod
    @transaction.atomic
    def processar_consumo_peca(peca_id: int, usuario=None):
        """
        Calcula e abate o estoque do material vinculado à peça bipada.
        """
        peca = Peca.objects.get(id=peca_id)
        
        # 1. Tentar encontrar o mapeamento do material
        mapeamento = MapeamentoMaterial.objects.filter(
            nome_dinabox=peca.material, 
            ativo=True
        ).first()

        if not mapeamento:
            # Se não houver mapeamento, não podemos abater estoque.
            # No futuro, isso pode gerar um alerta no dashboard de discrepâncias.
            return None

        # 2. Calcular consumo
        # Se for m2 (chapa), calculamos a área. Se for un, usamos a quantidade da peça.
        unidade = mapeamento.produto.unidade_medida
        consumo = Decimal("0")

        if unidade == 'm2':
            # Área em m2: (L * A) / 1.000.000
            if peca.largura_mm and peca.altura_mm:
                area = (Decimal(str(peca.largura_mm)) * Decimal(str(peca.altura_mm))) / Decimal("1000000")
                consumo = area * Decimal(str(peca.quantidade))
        else:
            # Consumo unitário
            consumo = Decimal(str(peca.quantidade))

        # Aplicar fator de conversão (margem de perda)
        consumo_final = consumo * mapeamento.fator_conversao

        # 3. Realizar a saída no estoque via MovimentacaoService
        # Como o estoque usa PositiveIntegerField para quantidade no MVP, 
        # vamos arredondar para cima para garantir que não falte material físico.
        # TODO: Avaliar se o estoque deve suportar decimais para m2.
        qtd_estoque = int(consumo_final.to_integral_value(rounding='ROUND_UP'))

        if qtd_estoque <= 0:
            return None

        mov_data = {
            'produto_id': mapeamento.produto.id,
            'tipo': 'saida',
            'quantidade': qtd_estoque,
            'observacao': f"Consumo automático (Gêmeo Digital) - Peça {peca.id_peca} / Lote {peca.numero_lote_pcp}"
        }

        return MovimentacaoService.processar_movimentacao(mov_data, usuario=usuario)
