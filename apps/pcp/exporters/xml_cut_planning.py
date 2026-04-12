# apps/pcp/exporters/xml_cut_planning.py
"""
Exportador XML para Cut Planning (CNC).

Responsabilidade: Gerar XML estruturado para máquinas de corte.
Padrão: XML validado, pronto para integração com softwares CNC.
"""

from typing import List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime

from apps.pcp.models.lote import LotePCP
from apps.pcp.models.plano_corte import PlanoCorte


class XMLCutPlanningExporter:
    """
    Exporta planos de corte em XML para máquinas CNC.
    
    Estrutura:
    <cutting_plan>
        <project>
        <plans>
            <plan>
                <pieces>
                    <piece>
                        <dimensions>
                        <material>
                        <edges>
    """
    
    @staticmethod
    def exportar(lote: LotePCP) -> str:
        """
        Exporta lote completo em XML para cut planning.
        
        Args:
            lote: LotePCP a exportar
            
        Returns:
            String XML formatada
        """
        root = Element('cutting_plan')
        root.set('version', '1.0')
        root.set('generated', datetime.now().isoformat())
        
        # Seção de Projeto
        XMLCutPlanningExporter._add_project_section(root, lote)
        
        # Seção de Planos
        XMLCutPlanningExporter._add_plans_section(root, lote)
        
        # Seção de Estatísticas
        XMLCutPlanningExporter._add_statistics_section(root, lote)
        
        # Formatar e retornar
        xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
        # Remover linhas vazias
        return "\n".join([line for line in xml_str.split("\n") if line.strip()])
    
    @staticmethod
    def _add_project_section(root: Element, lote: LotePCP) -> None:
        """Adiciona seção de projeto."""
        project = SubElement(root, 'project')
        
        SubElement(project, 'id').text = lote.pid
        SubElement(project, 'customer').text = lote.cliente_nome
        SubElement(project, 'description').text = lote.cliente_id_projeto or ""
        SubElement(project, 'date').text = lote.data_processamento.isoformat()
        SubElement(project, 'status').text = lote.status
    
    @staticmethod
    def _add_plans_section(root: Element, lote: LotePCP) -> None:
        """Adiciona seção de planos de corte."""
        plans_elem = SubElement(root, 'plans')
        
        planos = PlanoCorte.objects.filter(lote=lote).order_by('codigo_plano', 'numero_sequencial')
        
        for plano in planos:
            XMLCutPlanningExporter._add_plan_element(plans_elem, plano)
    
    @staticmethod
    def _add_plan_element(parent: Element, plano: PlanoCorte) -> None:
        """Adiciona elemento de plano individual."""
        plan = SubElement(parent, 'plan')
        plan.set('id', plano.codigo_completo)
        plan.set('type', plano.descricao_tipo)
        plan.set('status', plano.status)
        
        SubElement(plan, 'description').text = plano.descricao
        SubElement(plan, 'total_pieces').text = str(plano.total_pecas)
        SubElement(plan, 'estimated_time').text = str(plano.tempo_estimado_minutos)
        SubElement(plan, 'priority').text = str(plano.prioridade)
        
        # Adicionar peças
        pieces_elem = SubElement(plan, 'pieces')
        for peca in plano.pecas.all():
            XMLCutPlanningExporter._add_piece_element(pieces_elem, peca)
    
    @staticmethod
    def _add_piece_element(parent: Element, peca) -> None:
        """Adiciona elemento de peça."""
        piece = SubElement(parent, 'piece')
        piece.set('id', peca.codigo_peca)
        piece.set('quantity', str(peca.quantidade_planejada))
        
        SubElement(piece, 'description').text = peca.descricao
        SubElement(piece, 'material').text = peca.material or "Desconhecido"
        
        # Dimensões
        dimensions = SubElement(piece, 'dimensions')
        SubElement(dimensions, 'width').text = str(peca.comprimento or 0)
        SubElement(dimensions, 'height').text = str(peca.largura or 0)
        SubElement(dimensions, 'thickness').text = str(peca.espessura or 0)
        SubElement(dimensions, 'unit').text = "mm"
        
        # Bordas (se houver)
        if peca.atributos_tecnicos.get("bordas"):
            edges = SubElement(piece, 'edges')
            for borda_info in peca.atributos_tecnicos.get("bordas", []):
                borda = SubElement(edges, 'edge')
                SubElement(borda, 'position').text = borda_info.get("posicao", "")
                SubElement(borda, 'material').text = borda_info.get("material", "")
                SubElement(borda, 'width').text = str(borda_info.get("largura", 0))
    
    @staticmethod
    def _add_statistics_section(root: Element, lote: LotePCP) -> None:
        """Adiciona seção de estatísticas."""
        stats = SubElement(root, 'statistics')
        
        planos = PlanoCorte.objects.filter(lote=lote)
        total_pecas = sum(p.total_pecas for p in planos)
        total_tempo = sum(p.tempo_estimado_minutos for p in planos)
        
        SubElement(stats, 'total_plans').text = str(planos.count())
        SubElement(stats, 'total_pieces').text = str(total_pecas)
        SubElement(stats, 'total_estimated_time').text = str(total_tempo)
        SubElement(stats, 'average_time_per_piece').text = str(
            total_tempo // total_pecas if total_pecas > 0 else 0
        )
