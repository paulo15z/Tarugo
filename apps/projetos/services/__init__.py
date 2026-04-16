from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.pedidos.domain.status import AmbienteStatus, PedidoStatus
from apps.pedidos.models import Pedido
from apps.projetos.domain.status import ProjetoStatus
from apps.projetos.models import Projeto


class ProjetoService:
    @staticmethod
    @transaction.atomic
    def criar_projetos_iniciais_do_pedido(pedido: Pedido, usuario=None) -> list[Projeto]:
        projetos_criados: list[Projeto] = []
        for ambiente in pedido.ambientes.all().order_by("nome_ambiente"):
            projeto, criado = Projeto.objects.get_or_create(
                ambiente_pedido=ambiente,
                defaults={
                    "pedido": pedido,
                    "nome_projeto": f"Projeto Executivo {ambiente.nome_ambiente}",
                    "status": ProjetoStatus.AGUARDANDO_DEFINICOES,
                    "criado_por": usuario if getattr(usuario, "is_authenticated", False) else None,
                },
            )
            if not criado:
                campos = []
                if projeto.pedido_id != pedido.pk:
                    projeto.pedido = pedido
                    campos.append("pedido")
                if not projeto.nome_projeto:
                    projeto.nome_projeto = f"Projeto Executivo {ambiente.nome_ambiente}"
                    campos.append("nome_projeto")
                if campos:
                    campos.append("atualizado_em")
                    projeto.save(update_fields=campos)
            projetos_criados.append(projeto)
        return projetos_criados

    @staticmethod
    @transaction.atomic
    def atualizar_status(projeto: Projeto, novo_status: str, usuario=None, motivo: str = "") -> Projeto:
        status_validos = {value for value, _label in ProjetoStatus.choices}
        if novo_status not in status_validos:
            raise ValueError("Status de projeto invalido.")

        atual = projeto.status
        if atual == novo_status:
            return projeto

        transicoes_validas = {
            ProjetoStatus.AGUARDANDO_DEFINICOES: {ProjetoStatus.AGUARDANDO_PROJETISTA, ProjetoStatus.CANCELADO},
            ProjetoStatus.AGUARDANDO_PROJETISTA: {ProjetoStatus.EM_DESENVOLVIMENTO, ProjetoStatus.CANCELADO},
            ProjetoStatus.EM_DESENVOLVIMENTO: {ProjetoStatus.EM_CONFERENCIA, ProjetoStatus.CANCELADO},
            ProjetoStatus.EM_CONFERENCIA: {ProjetoStatus.AGUARDANDO_APROVACAO, ProjetoStatus.CANCELADO},
            ProjetoStatus.AGUARDANDO_APROVACAO: {ProjetoStatus.LIBERADO_PARA_PCP, ProjetoStatus.CANCELADO},
            ProjetoStatus.LIBERADO_PARA_PCP: set(),
            ProjetoStatus.CANCELADO: set(),
        }
        if novo_status not in transicoes_validas.get(atual, set()):
            raise ValueError(f"Transicao invalida: {atual} -> {novo_status}.")

        projeto.status = novo_status
        if novo_status == ProjetoStatus.EM_DESENVOLVIMENTO and projeto.data_inicio_real is None:
            projeto.data_inicio_real = timezone.now()
        if novo_status in {ProjetoStatus.LIBERADO_PARA_PCP, ProjetoStatus.CANCELADO}:
            projeto.data_fim_real = timezone.now()
        projeto.save()

        ambiente = projeto.ambiente_pedido
        if novo_status == ProjetoStatus.LIBERADO_PARA_PCP:
            ambiente.status = AmbienteStatus.AGUARDANDO_PCP
            ambiente.save(update_fields=["status", "data_atualizacao"])
            ProjetoService._recalcular_status_macro_do_pedido(projeto.pedido)
        elif novo_status == ProjetoStatus.CANCELADO:
            ambiente.status = AmbienteStatus.PENDENTE_PROJETOS
            ambiente.save(update_fields=["status", "data_atualizacao"])

        return projeto

    @staticmethod
    @transaction.atomic
    def atribuir_responsaveis(
        projeto: Projeto,
        distribuidor=None,
        projetista=None,
        liberador_tecnico=None,
    ) -> Projeto:
        update_fields = []
        if distribuidor is not None:
            projeto.distribuidor = distribuidor
            update_fields.append("distribuidor")
        if projetista is not None:
            projeto.projetista = projetista
            update_fields.append("projetista")
        if liberador_tecnico is not None:
            projeto.liberador_tecnico = liberador_tecnico
            update_fields.append("liberador_tecnico")
        if projeto.status == ProjetoStatus.AGUARDANDO_DEFINICOES and projeto.projetista_id:
            projeto.status = ProjetoStatus.AGUARDANDO_PROJETISTA
            update_fields.append("status")
        if update_fields:
            update_fields.append("atualizado_em")
            projeto.save(update_fields=update_fields)
        return projeto

    @staticmethod
    def _recalcular_status_macro_do_pedido(pedido: Pedido) -> None:
        todos_liberados = not pedido.projetos.exclude(status=ProjetoStatus.LIBERADO_PARA_PCP).exists()
        if todos_liberados and pedido.status == PedidoStatus.ENVIADO_PARA_PROJETOS:
            pedido.status = PedidoStatus.EM_ENGENHARIA
            pedido.save(update_fields=["status"])
