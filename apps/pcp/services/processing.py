# apps/pcp/services/processing.py
"""
Serviço Central de Processamento PCP 2.0.

Responsabilidade: Orquestrar processamento completo de projeto Dinabox.
Padrão: Recebe DinaboxProjectOperacional, retorna LotePCP com roteiros, ripas, planos e usinagem.
"""

from typing import List, Dict, Any, Tuple
from decimal import Decimal
from django.db import transaction

from apps.integracoes.dinabox.schemas import (
    DinaboxProjectOperacional,
    ModuleOperacional,
    PartOperacional,
)
from apps.pcp.models.lote import LotePCP, AmbientePCP, ModuloPCP, PecaPCP
from apps.pcp.models.roteiro import Roteiro, EtapaRoteiro
from apps.pcp.models.ripa import Ripa, OrigemRipa, DestinoRipa
from apps.pcp.services.ripa_service import RipaService
from apps.pcp.models.plano_corte import PlanoCorte, TipoPlanoCorte
from apps.pcp.models.usinagem import Usinagem, TipoUsinagem, FaceUsinagem
from apps.pcp.schemas.processamento import (
    ProcessamentoPCPSchema,
    RoteiroSchema,
    RipaSchema,
    PlanoCorteSchema,
    UsinagemSchema,
)


class PCPProcessingService:
    """
    Serviço central para processar projetos Dinabox completos.
    
    Fluxo:
    1. Recebe DinaboxProjectOperacional (validado)
    2. Cria LotePCP com hierarquia (Ambiente → Módulo → Peça)
    3. Gera roteiros para cada peça
    4. Consolida ripas por material/espessura
    5. Calcula planos de corte por tipo
    6. Mapeia operações de usinagem
    7. Retorna ProcessamentoPCPSchema com tudo
    """
    
    @staticmethod
    @transaction.atomic
    def processar_projeto(
        operacional: DinaboxProjectOperacional,
        usuario_id: int = None
    ) -> Tuple[LotePCP, ProcessamentoPCPSchema]:
        """
        Processa um projeto completo do Dinabox.
        
        Args:
            operacional: DinaboxProjectOperacional validado
            usuario_id: ID do usuário que disparou o processamento
            
        Returns:
            Tupla (LotePCP, ProcessamentoPCPSchema)
        """
        
        # 1. Criar LotePCP
        lote = PCPProcessingService._criar_lote(operacional, usuario_id)
        
        # 2. Gerar roteiros
        roteiros = PCPProcessingService._gerar_roteiros(lote, operacional)
        
        # 3. Consolidar ripas
        ripas = PCPProcessingService._consolidar_ripas(lote, operacional)
        
        # 4. Calcular planos de corte
        planos_corte = PCPProcessingService._calcular_planos_corte(lote, operacional)
        
        # 5. Mapear usinagem
        usinagens = PCPProcessingService._mapear_usinagem(lote, operacional)
        
        # 6. Montar schema de resposta
        schema = ProcessamentoPCPSchema(
            lote_id=lote.pid,
            cliente_nome=operacional.project_customer_name,
            projeto_descricao=operacional.project_description,
            roteiros=[RoteiroSchema.from_orm(r) for r in roteiros],
            ripas=[RipaSchema.from_orm(r) for r in ripas],
            planos_corte=[PlanoCorteSchema.from_orm(p) for p in planos_corte],
            usinagens=[UsinagemSchema.from_orm(u) for u in usinagens],
            total_pecas=lote.pecas_total,
            total_roteiros=len(roteiros),
            total_ripas=len(ripas),
            total_planos=len(planos_corte),
            total_usinagens=len(usinagens),
            tempo_total_estimado_minutos=sum(r.tempo_estimado_minutos for r in roteiros),
        )
        
        return lote, schema
    
    @staticmethod
    def _criar_lote(
        operacional: DinaboxProjectOperacional,
        usuario_id: int = None
    ) -> LotePCP:
        """Cria LotePCP com hierarquia completa."""
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        import uuid
        
        User = get_user_model()
        
        # Gerar PID único
        pid = f"L{timezone.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        
        # Criar LotePCP
        lote = LotePCP.objects.create(
            pid=pid,
            arquivo_original=f"dinabox-{operacional.project_id}",
            cliente_nome=operacional.project_customer_name,
            cliente_id_projeto=operacional.project_customer_id,
            ordem_producao=operacional.project_id,
            usuario=User.objects.get(id=usuario_id) if usuario_id else None,
        )
        
        # Criar Ambiente (usando project_description como nome)
        ambiente = AmbientePCP.objects.create(
            lote=lote,
            nome=operacional.project_description or "Sem Descrição"
        )
        
        # Criar Módulos e Peças
        total_pecas = 0
        for module in operacional.woodwork:
            modulo = ModuloPCP.objects.create(
                ambiente=ambiente,
                nome=module.name,
                codigo_modulo=module.ref or module.mid
            )
            
            # Criar peças do módulo
            for part in module.parts:
                peca = PecaPCP.objects.create(
                    modulo=modulo,
                    referencia_bruta=part.ref,
                    codigo_peca=part.ref,
                    descricao=part.name,
                    material=part.material_name,
                    codigo_material=part.material_id,
                    comprimento=Decimal(str(part.width)),
                    largura=Decimal(str(part.height)),
                    espessura=Decimal(str(part.thickness)),
                    quantidade_planejada=part.count or 1,
                    atributos_tecnicos={
                        "material_id": part.material_id,
                        "tipo_peca": part.type,
                        "face": part.material_face,
                    }
                )
                total_pecas += 1
        
        lote.pecas_total = total_pecas
        lote.save()
        
        return lote
    
    @staticmethod
    def _gerar_roteiros(
        lote: LotePCP,
        operacional: DinaboxProjectOperacional
    ) -> List[Roteiro]:
        """Gera roteiros para cada peça."""
        roteiros = []
        
        for peca in lote.pecas_all():
            # Determinar sequência de etapas
            sequencia = PCPProcessingService._determinar_sequencia_etapas(peca, operacional)
            
            # Estimar tempo
            tempo = PCPProcessingService._estimar_tempo_roteiro(peca, sequencia)
            
            # Criar roteiro
            roteiro = Roteiro.objects.create(
                peca=peca,
                sequencia=sequencia,
                tempo_estimado_minutos=tempo,
                observacoes=peca.observacoes or ""
            )
            roteiros.append(roteiro)
        
        return roteiros
    
    @staticmethod
    def _determinar_sequencia_etapas(peca: PecaPCP, operacional: DinaboxProjectOperacional) -> List[str]:
        """
        Determina sequência de etapas para uma peça.
        
        Lógica:
        1. Se tem bordas → BORDA
        2. Se tem furação → FURACAO
        3. Se é duplagem → DUPLAGEM
        4. Sempre termina com EXPEDICAO
        """
        sequencia = [EtapaRoteiro.CORTE]
        
        # Verificar se tem bordas
        if peca.atributos_tecnicos.get("tem_bordas"):
            sequencia.append(EtapaRoteiro.BORDA)
        
        # Verificar se tem furação
        if peca.atributos_tecnicos.get("tem_furacao"):
            sequencia.append(EtapaRoteiro.USINAGEM)
            sequencia.append(EtapaRoteiro.FURACAO)
        
        # Verificar se é duplagem
        if "duplagem" in (peca.observacoes or "").lower():
            sequencia.insert(1, EtapaRoteiro.DUPLAGEM)
        
        # Sempre termina com expedição
        sequencia.append(EtapaRoteiro.EXPEDICAO)
        
        return [e[0] for e in sequencia]  # Retorna apenas os códigos
    
    @staticmethod
    def _estimar_tempo_roteiro(peca: PecaPCP, sequencia: List[str]) -> int:
        """Estima tempo de roteiro baseado em etapas e dimensões."""
        tempo_base = 5  # minutos
        
        # Adicionar tempo por etapa
        tempo_por_etapa = {
            EtapaRoteiro.CORTE[0]: 10,
            EtapaRoteiro.DUPLAGEM[0]: 15,
            EtapaRoteiro.BORDA[0]: 20,
            EtapaRoteiro.USINAGEM[0]: 25,
            EtapaRoteiro.FURACAO[0]: 15,
            EtapaRoteiro.EXPEDICAO[0]: 5,
        }
        
        tempo = tempo_base
        for etapa in sequencia:
            tempo += tempo_por_etapa.get(etapa, 5)
        
        # Ajustar por tamanho
        area = float(peca.comprimento or 0) * float(peca.largura or 0) / 1_000_000
        if area > 1.0:
            tempo += int(area * 10)
        
        return tempo
    
    @staticmethod
    def _consolidar_ripas(
        lote: LotePCP,
        operacional: DinaboxProjectOperacional
    ) -> List[Ripa]:
        """
        Consolida ripas usando RipaService.
        
        Identifica peças com "_ripa_" na observação e as consolida em tiras
        otimizadas para corte/bordo, considerando serra (4.4mm) e refilo (5mm).
        """
        from apps.pcp.services.ripa_service import RipaService
        
        return RipaService.consolidar_ripas(lote)
    
    @staticmethod
    def _calcular_planos_corte(
        lote: LotePCP,
        operacional: DinaboxProjectOperacional
    ) -> List[PlanoCorte]:
        """
        Calcula planos de corte agrupando peças por tipo.
        
        Tipos: Chapa (03), Perfil (05), Porta (06), Gaveta (10), etc.
        """
        planos_map: Dict[str, List[PecaPCP]] = {}
        
        # Agrupar peças por tipo
        for peca in lote.pecas_all():
            tipo = PCPProcessingService._determinar_tipo_plano(peca)
            if tipo not in planos_map:
                planos_map[tipo] = []
            planos_map[tipo].append(peca)
        
        # Criar planos de corte
        planos = []
        numero_sequencial = 1
        for tipo, pecas in planos_map.items():
            plano = PlanoCorte.objects.create(
                lote=lote,
                codigo_plano=tipo,
                numero_sequencial=numero_sequencial,
                descricao=f"Plano de {dict(TipoPlanoCorte.choices).get(tipo, 'Outro')}",
                total_pecas=len(pecas),
                tempo_estimado_minutos=len(pecas) * 5,
                prioridade=1,
            )
            
            # Adicionar peças ao plano
            for peca in pecas:
                plano.adicionar_peca(peca)
            
            planos.append(plano)
            numero_sequencial += 1
        
        return planos
    
    @staticmethod
    def _determinar_tipo_plano(peca: PecaPCP) -> str:
        """Determina tipo de plano baseado na peça."""
        descricao = (peca.descricao or "").lower()
        
        if "porta" in descricao:
            return TipoPlanoCorte.PORTA
        elif "gaveta" in descricao:
            return TipoPlanoCorte.GAVETA
        elif "prateleira" in descricao:
            return TipoPlanoCorte.PRATELEIRA
        elif "frente" in descricao:
            return TipoPlanoCorte.FRENTE
        elif "lateral" in descricao:
            return TipoPlanoCorte.LATERAL
        elif "fundo" in descricao:
            return TipoPlanoCorte.FUNDO
        else:
            # Padrão: Chapa para pequenas, Perfil para grandes
            area = float(peca.comprimento or 0) * float(peca.largura or 0)
            return TipoPlanoCorte.CHAPA if area < 1_000_000 else TipoPlanoCorte.PERFIL
    
    @staticmethod
    def _mapear_usinagem(
        lote: LotePCP,
        operacional: DinaboxProjectOperacional
    ) -> List[Usinagem]:
        """
        Mapeia operações de usinagem (furação, rasgos, etc.).
        
        Extrai dados de holes e cria registros de Usinagem.
        """
        usinagens = []
        
        # Iterar sobre módulos e peças
        for module in operacional.woodwork:
            for part in module.parts:
                peca_db = lote.pecas_all().filter(codigo_peca=part.ref).first()
                if not peca_db:
                    continue
                
                # Mapear furos por face
                if part.holes:
                    for face_code, holes_list in part.holes.items():
                        if not holes_list:
                            continue
                        
                        # Cada furo é uma operação
                        for hole in holes_list:
                            usinagem = Usinagem.objects.create(
                                peca=peca_db,
                                tipo=TipoUsinagem.FURO,
                                face=face_code,
                                coordenada_x=Decimal(str(hole.get("x", 0))),
                                coordenada_y=Decimal(str(hole.get("y", 0))),
                                diametro_mm=Decimal(str(hole.get("d", 0))),
                                profundidade_mm=Decimal(str(hole.get("depth", 0))),
                                quantidade=1,
                            )
                            usinagens.append(usinagem)
        
        return usinagens
