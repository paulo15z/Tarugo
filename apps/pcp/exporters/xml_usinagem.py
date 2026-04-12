# apps/pcp/exporters/xml_usinagem.py
"""
Exportador XML para Usinagem (Furação, Rasgos, etc.).

Responsabilidade: Gerar XML estruturado para máquinas de usinagem.
Padrão: XML com coordenadas, diâmetros e profundidades para CNC.
"""

from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime

from apps.pcp.models.lote import LotePCP
from apps.pcp.models.usinagem import Usinagem


class XMLUsinagemExporter:
    """
    Exporta operações de usinagem em XML para máquinas CNC.
    
    Estrutura:
    <machining_plan>
        <project>
        <operations>
            <piece>
                <face>
                    <operation>
                        <coordinates>
                        <parameters>
    """
    
    @staticmethod
    def exportar(lote: LotePCP) -> str:
        """
        Exporta operações de usinagem em XML.
        
        Args:
            lote: LotePCP a exportar
            
        Returns:
            String XML formatada
        """
        root = Element('machining_plan')
        root.set('version', '1.0')
        root.set('generated', datetime.now().isoformat())
        
        # Seção de Projeto
        XMLUsinagemExporter._add_project_section(root, lote)
        
        # Seção de Operações
        XMLUsinagemExporter._add_operations_section(root, lote)
        
        # Seção de Estatísticas
        XMLUsinagemExporter._add_statistics_section(root, lote)
        
        # Formatar e retornar
        xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
        return "\n".join([line for line in xml_str.split("\n") if line.strip()])
    
    @staticmethod
    def _add_project_section(root: Element, lote: LotePCP) -> None:
        """Adiciona seção de projeto."""
        project = SubElement(root, 'project')
        
        SubElement(project, 'id').text = lote.pid
        SubElement(project, 'customer').text = lote.cliente_nome
        SubElement(project, 'description').text = lote.cliente_id_projeto or ""
        SubElement(project, 'date').text = lote.data_processamento.isoformat()
    
    @staticmethod
    def _add_operations_section(root: Element, lote: LotePCP) -> None:
        """Adiciona seção de operações de usinagem."""
        operations = SubElement(root, 'operations')
        
        # Agrupar usinagens por peça
        usinagens_por_peca = {}
        for usinagem in Usinagem.objects.filter(peca__modulo__ambiente__lote=lote):
            peca_id = usinagem.peca.id
            if peca_id not in usinagens_por_peca:
                usinagens_por_peca[peca_id] = []
            usinagens_por_peca[peca_id].append(usinagem)
        
        # Adicionar peças com operações
        for peca_id, usinagens in usinagens_por_peca.items():
            usinagem_primeira = usinagens[0]
            peca = usinagem_primeira.peca
            XMLUsinagemExporter._add_piece_element(operations, peca, usinagens)
    
    @staticmethod
    def _add_piece_element(parent: Element, peca, usinagens: list) -> None:
        """Adiciona elemento de peça com suas operações."""
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
        
        # Agrupar operações por face
        operacoes_por_face = {}
        for usinagem in usinagens:
            face = usinagem.face
            if face not in operacoes_por_face:
                operacoes_por_face[face] = []
            operacoes_por_face[face].append(usinagem)
        
        # Adicionar operações por face
        faces_elem = SubElement(piece, 'faces')
        for face, operacoes in operacoes_por_face.items():
            XMLUsinagemExporter._add_face_element(faces_elem, face, operacoes)
    
    @staticmethod
    def _add_face_element(parent: Element, face: str, operacoes: list) -> None:
        """Adiciona elemento de face com suas operações."""
        face_elem = SubElement(parent, 'face')
        face_elem.set('id', face)
        face_elem.set('total_operations', str(len(operacoes)))
        
        # Adicionar operações
        for usinagem in operacoes:
            XMLUsinagemExporter._add_operation_element(face_elem, usinagem)
    
    @staticmethod
    def _add_operation_element(parent: Element, usinagem) -> None:
        """Adiciona elemento de operação individual."""
        operation = SubElement(parent, 'operation')
        operation.set('id', str(usinagem.id))
        operation.set('type', usinagem.get_tipo_display())
        operation.set('status', usinagem.status)
        
        # Coordenadas
        coordinates = SubElement(operation, 'coordinates')
        SubElement(coordinates, 'x').text = str(usinagem.coordenada_x)
        SubElement(coordinates, 'y').text = str(usinagem.coordenada_y)
        SubElement(coordinates, 'unit').text = "mm"
        
        # Parâmetros
        parameters = SubElement(operation, 'parameters')
        
        if usinagem.diametro_mm:
            SubElement(parameters, 'diameter').text = str(usinagem.diametro_mm)
        
        if usinagem.profundidade_mm:
            SubElement(parameters, 'depth').text = str(usinagem.profundidade_mm)
        
        if usinagem.largura_mm:
            SubElement(parameters, 'width').text = str(usinagem.largura_mm)
        
        if usinagem.comprimento_mm:
            SubElement(parameters, 'length').text = str(usinagem.comprimento_mm)
        
        if usinagem.quantidade > 1:
            SubElement(parameters, 'quantity').text = str(usinagem.quantidade)
        
        # Observações
        if usinagem.observacoes:
            SubElement(operation, 'notes').text = usinagem.observacoes
    
    @staticmethod
    def _add_statistics_section(root: Element, lote: LotePCP) -> None:
        """Adiciona seção de estatísticas."""
        stats = SubElement(root, 'statistics')
        
        usinagens = Usinagem.objects.filter(peca__modulo__ambiente__lote=lote)
        total_operacoes = usinagens.count()
        
        # Contar por tipo
        tipos = {}
        for usinagem in usinagens:
            tipo = usinagem.get_tipo_display()
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        SubElement(stats, 'total_operations').text = str(total_operacoes)
        SubElement(stats, 'total_pieces').text = str(
            usinagens.values('peca').distinct().count()
        )
        
        # Operações por tipo
        types_elem = SubElement(stats, 'operations_by_type')
        for tipo, count in tipos.items():
            type_elem = SubElement(types_elem, 'type')
            type_elem.set('name', tipo)
            type_elem.text = str(count)
