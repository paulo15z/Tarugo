"""
Services para o app pedidos.

Responsabilidade: TODA lógica de negócio reside aqui.
Padrão: Recebe dados validados (Pydantic), retorna schemas tipados.
"""

from django.db import transaction
from datetime import datetime
from typing import Optional

from apps.pedidos.domain.status import PedidoStatus, AmbienteStatus
from apps.pedidos.models import Pedido, AmbientePedido, HistoricoStatusPedido
from apps.comercial.models import ClienteComercial, AmbienteOrcamento


class PedidoService:
    """
    Serviço central para gerenciar o ciclo de vida de pedidos.
    """

    @staticmethod
    @transaction.atomic
    def criar_pedido_do_comercial(
        cliente_comercial: ClienteComercial,
        numero_pedido: str,
        usuario=None,
    ) -> Pedido:
        """
        Cria um novo Pedido a partir de um ClienteComercial.

        Fluxo:
        1. Valida se numero_pedido já existe
        2. Cria Pedido com status CONTRATO_FECHADO
        3. Cria AmbientePedido para cada AmbienteOrcamento do cliente
        4. Registra no histórico

        Args:
            cliente_comercial: Instância de ClienteComercial
            numero_pedido: Identificador único do pedido
            usuario: Usuário que criou o pedido (opcional)

        Raises:
            ValueError: Se numero_pedido já existe

        Returns:
            Instância do Pedido criado
        """
        if Pedido.objects.filter(numero_pedido=numero_pedido).exists():
            raise ValueError(f"Número de pedido {numero_pedido} já existe.")

        # Criar Pedido
        pedido = Pedido.objects.create(
            numero_pedido=numero_pedido,
            customer_id=cliente_comercial.customer_id,
            cliente_nome=cliente_comercial.nome_cliente,
            cliente_comercial=cliente_comercial,
            status=PedidoStatus.CONTRATO_FECHADO,
            data_contrato=cliente_comercial.data_contrato,
            criado_por=usuario,
        )

        # Registrar no histórico
        HistoricoStatusPedido.objects.create(
            pedido=pedido,
            status_anterior="",
            status_novo=PedidoStatus.CONTRATO_FECHADO,
            motivo="Criação do pedido a partir do fechamento de contrato no Comercial.",
            usuario=usuario,
        )

        # Criar ambientes a partir do Comercial
        for ambiente_orcamento in cliente_comercial.ambientes.all():
            AmbientePedido.objects.create(
                pedido=pedido,
                nome_ambiente=ambiente_orcamento.nome_ambiente,
                descricao=ambiente_orcamento.descricao,
                acabamentos=ambiente_orcamento.acabamentos,
                eletrodomesticos=ambiente_orcamento.eletrodomesticos,
                observacoes_especiais=ambiente_orcamento.observacoes_especiais,
                status=AmbienteStatus.PENDENTE,
            )

        return pedido

    @staticmethod
    @transaction.atomic
    def atualizar_status_pedido(
        pedido: Pedido,
        novo_status: str,
        motivo: str = "",
        usuario=None,
    ) -> Pedido:
        """
        Atualiza o status de um Pedido e registra a transição.

        Args:
            pedido: Instância do Pedido
            novo_status: Novo status (deve estar em PedidoStatus.choices)
            motivo: Motivo da transição (opcional)
            usuario: Usuário que fez a transição (opcional)

        Raises:
            ValueError: Se novo_status é inválido

        Returns:
            Pedido atualizado
        """
        status_validos = [choice[0] for choice in PedidoStatus.choices]
        if novo_status not in status_validos:
            raise ValueError(f"Status inválido: {novo_status}")

        status_anterior = pedido.status

        # Atualizar se status é diferente
        if status_anterior != novo_status:
            pedido.status = novo_status

            # Atualizar data_conclusao se transitando para CONCLUIDO
            if novo_status == PedidoStatus.CONCLUIDO:
                pedido.data_conclusao = datetime.now()

            pedido.save()

            # Registrar no histórico
            HistoricoStatusPedido.objects.create(
                pedido=pedido,
                status_anterior=status_anterior,
                status_novo=novo_status,
                motivo=motivo,
                usuario=usuario,
            )

        return pedido

    @staticmethod
    @transaction.atomic
    def processar_engenharia_ambiente(
        ambiente: AmbientePedido,
        dados_engenharia: dict,
        usuario=None,
    ) -> AmbientePedido:
        """
        Atualiza dados de engenharia de um ambiente (via Dinabox API).

        Fluxo:
        1. Atualiza dados_engenharia do ambiente
        2. Muda status para AGUARDANDO_PCP
        3. Verifica se todos os ambientes estão em engenharia concluída
            - Se sim, muda pedido para EM_ENGENHARIA

        Args:
            ambiente: Instância de AmbientePedido
            dados_engenharia: Dict com dados extraídos da API Dinabox
            usuario: Usuário que processou (opcional)

        Returns:
            AmbientePedido atualizado
        """
        ambiente.dados_engenharia = dados_engenharia
        ambiente.status = AmbienteStatus.AGUARDANDO_PCP
        ambiente.save()

        # Verificar se todos os ambientes esperando PCP
        pedido = ambiente.pedido
        ambientes_nao_aguardando = pedido.ambientes.exclude(
            status__in=[
                AmbienteStatus.AGUARDANDO_PCP,
                AmbienteStatus.EM_INDUSTRIA,
                AmbienteStatus.EM_MONTAGEM,
                AmbienteStatus.CONCLUIDO,
            ]
        ).count()

        # Se não há ambientes em status anterior, atualizar pedido
        if ambientes_nao_aguardando == 0 and pedido.status == PedidoStatus.CONTRATO_FECHADO:
            PedidoService.atualizar_status_pedido(
                pedido,
                PedidoStatus.EM_ENGENHARIA,
                "Todos os ambientes concluíram engenharia.",
                usuario,
            )

        return ambiente

    @staticmethod
    @transaction.atomic
    def vincular_lote_pcp(
        ambiente: AmbientePedido,
        lote_pcp,
        metricas_pcp: dict,
        usuario=None,
    ) -> AmbientePedido:
        """
        Vincula um lote PCP a um ambiente e atualiza métricas.

        Fluxo:
        1. Associa lote PCP ao ambiente
        2. Atualiza metricas_pcp_resumo
        3. Muda status para EM_INDUSTRIA
        4. Verifica se todos ambientes estão em produção
            - Se sim, muda pedido para EM_PRODUCAO

        Args:
            ambiente: Instância de AmbientePedido
            lote_pcp: Instância de LotePCP (do app pcp)
            metricas_pcp: Dict com métricas do PCP
            usuario: Usuário que vinculou (opcional)

        Returns:
            AmbientePedido atualizado
        """
        ambiente.lotes_pcp.add(lote_pcp)
        ambiente.metricas_pcp_resumo = metricas_pcp
        ambiente.status = AmbienteStatus.EM_INDUSTRIA
        ambiente.save()

        # Verificar se todos os ambientes estão em produção
        pedido = ambiente.pedido
        ambientes_nao_producao = pedido.ambientes.exclude(
            status__in=[
                AmbienteStatus.EM_INDUSTRIA,
                AmbienteStatus.EM_MONTAGEM,
                AmbienteStatus.CONCLUIDO,
            ]
        ).count()

        # Se todos os ambientes estão em produção, atualizar pedido
        if ambientes_nao_producao == 0 and pedido.status == PedidoStatus.EM_ENGENHARIA:
            PedidoService.atualizar_status_pedido(
                pedido,
                PedidoStatus.EM_PRODUCAO,
                "Todos os ambientes iniciaram produção.",
                usuario,
            )

        return ambiente

    @staticmethod
    @transaction.atomic
    def atualizar_dados_operacionais(
        ambiente: AmbientePedido,
        dados_operacionais: dict,
    ) -> AmbientePedido:
        """
        Atualiza dados operacionais (bipagem, expedição, etc).

        Args:
            ambiente: Instância de AmbientePedido
            dados_operacionais: Dict com dados de bipagem/expedição

        Returns:
            AmbientePedido atualizado
        """
        ambiente.dados_operacionais_resumo = dados_operacionais

        # Se 100% bipado e expedido, marcar como concluído
        total_pecas = ambiente.num_pecas_pcp or 1
        pecas_expedidas = dados_operacionais.get("pecas_expedidas", 0)

        if pecas_expedidas >= total_pecas and total_pecas > 0:
            ambiente.status = AmbienteStatus.CONCLUIDO
            # TODO: Verificar se pedido deve ser concluído

        ambiente.save()
        return ambiente

    @staticmethod
    def obter_pedido_por_numero(numero_pedido: str) -> Optional[Pedido]:
        """Busca um pedido pelo número."""
        return Pedido.objects.filter(numero_pedido=numero_pedido).first()

    @staticmethod
    def obter_pedidos_por_cliente(customer_id: str):
        """Lista todos os pedidos de um cliente."""
        return Pedido.objects.filter(customer_id=customer_id).order_by("-data_criacao")
