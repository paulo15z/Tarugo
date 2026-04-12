# apps/pcp/services/ripa_service.py
"""
Serviço de Consolidação de Ripas para Otimização de Corte/Bordo.

Responsabilidade: Consolidar peças marcadas com "_ripa_" em tiras otimizadas.
Padrão: Agrupa por largura, distribui em grandes tiras, desconta serra e refilo.
"""

from typing import List, Dict, Tuple
from decimal import Decimal
from dataclasses import dataclass

from apps.pcp.models.lote import LotePCP, PecaPCP
from apps.pcp.models.ripa import Ripa, OrigemRipa, DestinoRipa


@dataclass
class ConfiguracaoRipa:
    """Configuração de parâmetros para cálculo de ripas."""
    
    altura_chapa_mm: Decimal = Decimal(2750)  # Altura padrão de chapa
    largura_chapa_mm: Decimal = Decimal(1830)  # Largura padrão de chapa
    serra_mm: Decimal = Decimal(4.4)  # Espessura da serra
    margem_refilo_mm: Decimal = Decimal(5)  # Margem de refilo (cada lado)
    
    @property
    def desconto_altura(self) -> Decimal:
        """Desconto total na altura (serra + 2x refilo)."""
        return self.serra_mm + (2 * self.margem_refilo_mm)
    
    @property
    def desconto_largura(self) -> Decimal:
        """Desconto total na largura (serra + 2x refilo)."""
        return self.serra_mm + (2 * self.margem_refilo_mm)


class RipaService:
    """
    Serviço para consolidação de ripas.
    
    Fluxo:
    1. Identificar peças com "_ripa_" na observação
    2. Agrupar por largura da peça
    3. Para cada grupo, calcular tiras otimizadas
    4. Considerar serra (4.4mm) e refilo (5mm cada lado)
    5. Criar registros de Ripa consolidados
    """
    
    @staticmethod
    def consolidar_ripas(
        lote: LotePCP,
        config: ConfiguracaoRipa = None
    ) -> List[Ripa]:
        """
        Consolida ripas a partir de peças marcadas com "_ripa_".
        
        Args:
            lote: LotePCP para consolidar
            config: Configuração de parâmetros
            
        Returns:
            Lista de Ripa consolidadas
        """
        if config is None:
            config = ConfiguracaoRipa()
        
        # 1. Identificar peças ripadas
        pecas_ripadas = RipaService._identificar_pecas_ripadas(lote)
        
        if not pecas_ripadas:
            return []
        
        # 2. Agrupar por (material, espessura, largura)
        grupos = RipaService._agrupar_pecas_ripadas(pecas_ripadas)
        
        # 3. Calcular tiras para cada grupo
        ripas = []
        numero_sequencial = 1
        
        for (material, espessura, largura_peca), pecas in grupos.items():
            tiras = RipaService._calcular_tiras(
                pecas=pecas,
                largura_peca=largura_peca,
                config=config
            )
            
            # 4. Criar registros de Ripa
            for tira in tiras:
                ripa = Ripa.objects.create(
                    lote=lote,
                    codigo_ripa=f"RIP-{lote.pid}-{numero_sequencial:03d}",
                    material_name=material or "Desconhecido",
                    material_id=pecas[0].atributos_tecnicos.get("material_id", ""),
                    espessura_mm=espessura,
                    comprimento_mm=tira["comprimento"],
                    largura_mm=tira["largura"],
                    quantidade=tira["quantidade"],
                    origem=OrigemRipa.CORTE,
                    destino=DestinoRipa.PENDENTE,
                    observacoes=f"Consolidação de {tira['total_pecas']} peças ripadas"
                )
                ripas.append(ripa)
                numero_sequencial += 1
        
        return ripas
    
    @staticmethod
    def _identificar_pecas_ripadas(lote: LotePCP) -> List[PecaPCP]:
        """Identifica peças marcadas com '_ripa_' na observação."""
        pecas_ripadas = []
        
        for peca in lote.pecas_all():
            observacoes = (peca.observacoes or "").lower()
            if "_ripa_" in observacoes or "ripa" in observacoes:
                pecas_ripadas.append(peca)
        
        return pecas_ripadas
    
    @staticmethod
    def _agrupar_pecas_ripadas(
        pecas: List[PecaPCP]
    ) -> Dict[Tuple[str, Decimal, Decimal], List[PecaPCP]]:
        """
        Agrupa peças por (material, espessura, largura).
        
        A largura é a dimensão crítica para consolidação.
        """
        grupos = {}
        
        for peca in pecas:
            # Usar a menor dimensão como "largura" (para ripas)
            dimensoes = sorted([
                float(peca.comprimento or 0),
                float(peca.largura or 0)
            ])
            
            largura_peca = Decimal(str(dimensoes[0]))
            espessura = peca.espessura or Decimal(0)
            material = peca.material or "Desconhecido"
            
            chave = (material, espessura, largura_peca)
            
            if chave not in grupos:
                grupos[chave] = []
            
            grupos[chave].append(peca)
        
        return grupos
    
    @staticmethod
    def _calcular_tiras(
        pecas: List[PecaPCP],
        largura_peca: Decimal,
        config: ConfiguracaoRipa
    ) -> List[Dict]:
        """
        Calcula tiras otimizadas para um grupo de peças.
        
        Lógica:
        1. Calcular altura total necessária (soma de comprimentos)
        2. Considerar serra (4.4mm) entre peças
        3. Distribuir em tiras (altura máx = altura_chapa - refilo)
        4. Retornar tiras com comprimento, largura, quantidade
        """
        
        # Calcular altura total necessária
        altura_total = Decimal(0)
        for peca in pecas:
            # Usar a maior dimensão como "comprimento" (altura da peça)
            dimensoes = sorted([
                float(peca.comprimento or 0),
                float(peca.largura or 0)
            ], reverse=True)
            altura_total += Decimal(str(dimensoes[0]))
        
        # Adicionar serra entre peças (n-1 serras)
        if len(pecas) > 1:
            altura_total += config.serra_mm * (len(pecas) - 1)
        
        # Altura disponível por tira (desconta refilo)
        altura_disponivel = config.altura_chapa_mm - config.desconto_altura
        
        # Calcular número de tiras necessárias
        num_tiras = (altura_total + altura_disponivel - 1) // altura_disponivel
        if num_tiras == 0:
            num_tiras = 1
        
        # Distribuir altura entre tiras
        altura_por_tira = altura_total / num_tiras
        
        # Largura da tira (desconta refilo)
        largura_tira = largura_peca - config.desconto_largura
        
        # Criar tiras
        tiras = []
        for i in range(int(num_tiras)):
            tira = {
                "comprimento": altura_por_tira,
                "largura": largura_tira,
                "quantidade": 1,
                "total_pecas": len(pecas),
                "sequencia": i + 1
            }
            tiras.append(tira)
        
        return tiras
    
    @staticmethod
    def calcular_area_ripa(ripa: Ripa) -> Decimal:
        """Calcula área de uma ripa em m²."""
        return (ripa.comprimento_mm * ripa.largura_mm) / Decimal(1_000_000)
    
    @staticmethod
    def calcular_volume_ripa(ripa: Ripa) -> Decimal:
        """Calcula volume de uma ripa em m³."""
        area = RipaService.calcular_area_ripa(ripa)
        return area * (ripa.espessura_mm / Decimal(1000))
    
    @staticmethod
    def agrupar_ripas_por_material(ripas: List[Ripa]) -> Dict[str, List[Ripa]]:
        """Agrupa ripas por material para visualização."""
        grupos = {}
        
        for ripa in ripas:
            material = ripa.material_name
            if material not in grupos:
                grupos[material] = []
            grupos[material].append(ripa)
        
        return grupos
    
    @staticmethod
    def calcular_totais_ripas(ripas: List[Ripa]) -> Dict:
        """Calcula totais consolidados de ripas."""
        total_ripas = len(ripas)
        total_area = sum(RipaService.calcular_area_ripa(r) for r in ripas)
        total_volume = sum(RipaService.calcular_volume_ripa(r) for r in ripas)
        
        # Agrupar por material
        por_material = RipaService.agrupar_ripas_por_material(ripas)
        materiais_count = {m: len(rs) for m, rs in por_material.items()}
        
        return {
            "total_ripas": total_ripas,
            "total_area_m2": float(total_area),
            "total_volume_m3": float(total_volume),
            "ripas_por_material": materiais_count,
            "materiais": list(por_material.keys())
        }
