from __future__ import annotations

from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.db import transaction

from apps.integracoes.dinabox.client import DinaboxAPIClient, DinaboxRequestError
from apps.integracoes.services import DinaboxClienteService

from ..models import AmbienteOrcamento, ClienteComercial, ObservacaoComercial, StatusClienteComercial
from ..schemas.cliente import (
    AmbienteOrcamentoInputSchema,
    AmbienteOrcamentoAtualizarSchema,
    AmbienteDetalhesInputSchema,
    ClienteComercialAtualizarDinaboxSchema,
    ClienteComercialCriarDinaboxSchema,
    ClienteComercialNumeroPedidoSchema,
)


def _montar_pf_pj(schema: ClienteComercialCriarDinaboxSchema | ClienteComercialAtualizarDinaboxSchema):
    pf = None
    pj = None
    if schema.customer_type == "pf" and getattr(schema, "customer_cpf", None):
        pf = {"cpf": schema.customer_cpf}
    if schema.customer_type == "pj" and getattr(schema, "customer_cnpj", None):
        pj = {"cnpj": schema.customer_cnpj}
    return pf, pj


def _extrair_customer_id(payload: dict) -> str:
    for key in ("customer_id", "id", "customerId"):
        raw = payload.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    raise ValueError("A API Dinabox não retornou o identificador do cliente (customer_id).")


class ClienteComercialService:
    """
    Regras de negócio do comercial no Tarugo.

    A API Dinabox é usada só para cadastro essencial do cliente (criar/atualizar/apagar e
    sincronizar índice). Acompanhamento (status, observações, ambientes/valores) é 100% Tarugo.
    """

    @staticmethod
    @transaction.atomic
    def criar_na_dinabox_e_local(
        schema: ClienteComercialCriarDinaboxSchema,
        usuario: Optional[AbstractUser],
    ) -> ClienteComercial:
        api = DinaboxAPIClient()
        pf, pj = _montar_pf_pj(schema)
        created = api.create_customer(
            customer_name=schema.customer_name,
            customer_type=schema.customer_type,
            customer_status=schema.customer_status,
            customer_emails=schema.customer_emails,
            customer_phones=schema.customer_phones,
            customer_pf_data=pf,
            customer_pj_data=pj,
            customer_note=schema.customer_note,
        )
        if not isinstance(created, dict):
            raise ValueError("Resposta inválida ao criar cliente na Dinabox.")

        customer_id = _extrair_customer_id(created)
        DinaboxClienteService.refresh_from_remote(customer_id)

        if ClienteComercial.objects.filter(customer_id=customer_id).exists():
            raise ValueError("Cliente já possui ficha comercial vinculada.")

        return ClienteComercial.objects.create(
            customer_id=customer_id,
            status=StatusClienteComercial.PRIMEIRO_CONTATO,
            criado_por=usuario if usuario and usuario.is_authenticated else None,
        )

    @staticmethod
    @transaction.atomic
    def vincular_cliente_existente(customer_id: str, usuario: Optional[AbstractUser]) -> ClienteComercial:
        cid = str(customer_id or "").strip()
        if not cid:
            raise ValueError("customer_id é obrigatório.")
        if ClienteComercial.objects.filter(customer_id=cid).exists():
            raise ValueError("Este cliente já está vinculado ao comercial.")

        DinaboxClienteService.refresh_from_remote(cid)

        return ClienteComercial.objects.create(
            customer_id=cid,
            status=StatusClienteComercial.PRIMEIRO_CONTATO,
            criado_por=usuario if usuario and usuario.is_authenticated else None,
        )

    @staticmethod
    @transaction.atomic
    def atualizar_cadastro_dinabox(
        cliente: ClienteComercial,
        schema: ClienteComercialAtualizarDinaboxSchema,
    ) -> None:
        if str(schema.customer_id).strip() != str(cliente.customer_id).strip():
            raise ValueError("customer_id inconsistente.")

        api = DinaboxAPIClient()
        pf, pj = _montar_pf_pj(schema)
        api.update_customer(
            customer_id=cliente.customer_id,
            customer_name=schema.customer_name,
            customer_type=schema.customer_type,
            customer_status=schema.customer_status,
            customer_emails=schema.customer_emails,
            customer_phones=schema.customer_phones,
            customer_pf_data=pf,
            customer_pj_data=pj,
            customer_note=schema.customer_note,
        )
        DinaboxClienteService.refresh_from_remote(cliente.customer_id)

    @staticmethod
    @transaction.atomic
    def atualizar_status(cliente: ClienteComercial, status: str) -> ClienteComercial:
        validos = {c.value for c in StatusClienteComercial}
        if status not in validos:
            raise ValueError("Status inválido.")
        cliente.status = status
        cliente.save(update_fields=["status", "atualizado_em"])
        return cliente

    @staticmethod
    @transaction.atomic
    def atualizar_numero_pedido(
        cliente: ClienteComercial,
        schema: ClienteComercialNumeroPedidoSchema,
    ) -> ClienteComercial:
        numero_pedido = schema.numero_pedido or ""
        if numero_pedido:
            if (
                ClienteComercial.objects.exclude(pk=cliente.pk)
                .filter(numero_pedido=numero_pedido)
                .exists()
            ):
                raise ValueError("Este numero de pedido ja esta vinculado a outro cliente comercial.")

            from apps.pedidos.models import Pedido

            if Pedido.objects.exclude(cliente_comercial=cliente).filter(numero_pedido=numero_pedido).exists():
                raise ValueError("Este numero de pedido ja existe no app Pedidos.")

        cliente.numero_pedido = numero_pedido
        cliente.save(update_fields=["numero_pedido", "atualizado_em"])
        return cliente

    @staticmethod
    @transaction.atomic
    def adicionar_observacao(cliente: ClienteComercial, texto: str, autor: Optional[AbstractUser]) -> ObservacaoComercial:
        t = (texto or "").strip()
        if not t:
            raise ValueError("Texto da observação é obrigatório.")
        return ObservacaoComercial.objects.create(
            cliente=cliente,
            texto=t,
            autor=autor if autor and autor.is_authenticated else None,
        )

    @staticmethod
    @transaction.atomic
    def adicionar_ambiente(cliente: ClienteComercial, schema: AmbienteOrcamentoInputSchema) -> AmbienteOrcamento:
        ultima = cliente.ambientes.order_by("-ordem").first()
        ordem = (ultima.ordem + 1) if ultima else 0
        return AmbienteOrcamento.objects.create(
            cliente=cliente,
            nome_ambiente=schema.nome_ambiente,
            valor_orcado=schema.valor_orcado,
            ordem=ordem,
        )

    @staticmethod
    @transaction.atomic
    def atualizar_ambiente(
        ambiente: AmbienteOrcamento,
        schema: AmbienteOrcamentoInputSchema,
    ) -> AmbienteOrcamento:
        ambiente.nome_ambiente = schema.nome_ambiente
        ambiente.valor_orcado = schema.valor_orcado
        ambiente.save(update_fields=["nome_ambiente", "valor_orcado", "atualizado_em"])
        return ambiente

    @staticmethod
    @transaction.atomic
    def atualizar_detalhes_ambiente(
        ambiente: AmbienteOrcamento,
        schema: AmbienteDetalhesInputSchema,
    ) -> AmbienteOrcamento:
        """Atualizar apenas os detalhes do ambiente (acabamentos, eletros, obs)."""
        ambiente.acabamentos = schema.acabamentos or []
        ambiente.eletrodomesticos = schema.eletrodomesticos or []
        ambiente.observacoes_especiais = schema.observacoes_especiais or ""
        ambiente.save(update_fields=["acabamentos", "eletrodomesticos", "observacoes_especiais", "atualizado_em"])
        return ambiente

    @staticmethod
    @transaction.atomic
    def atualizar_ambiente_completo(
        ambiente: AmbienteOrcamento,
        schema: AmbienteOrcamentoAtualizarSchema,
    ) -> AmbienteOrcamento:
        """Atualizar ambiente com todos os campos (nome, valor, detalhes)."""
        if schema.nome_ambiente is not None:
            ambiente.nome_ambiente = schema.nome_ambiente
        if schema.valor_orcado is not None:
            ambiente.valor_orcado = schema.valor_orcado
        if schema.acabamentos is not None:
            ambiente.acabamentos = schema.acabamentos
        if schema.eletrodomesticos is not None:
            ambiente.eletrodomesticos = schema.eletrodomesticos
        if schema.observacoes_especiais is not None:
            ambiente.observacoes_especiais = schema.observacoes_especiais
        
        ambiente.save(update_fields=[
            "nome_ambiente", "valor_orcado", "acabamentos",
            "eletrodomesticos", "observacoes_especiais", "atualizado_em"
        ])
        return ambiente

    @staticmethod
    def adicionar_acabamento(ambiente: AmbienteOrcamento, acabamento: str) -> AmbienteOrcamento:
        """Adicionar um acabamento à lista."""
        acc = (acabamento or "").strip()
        if not acc:
            raise ValueError("Acabamento não pode ser vazio.")
        if acc not in ambiente.acabamentos:
            ambiente.acabamentos.append(acc)
            ambiente.save(update_fields=["acabamentos", "atualizado_em"])
        return ambiente

    @staticmethod
    def remover_acabamento(ambiente: AmbienteOrcamento, acabamento: str) -> AmbienteOrcamento:
        """Remover um acabamento da lista."""
        acc = (acabamento or "").strip()
        if acc in ambiente.acabamentos:
            ambiente.acabamentos.remove(acc)
            ambiente.save(update_fields=["acabamentos", "atualizado_em"])
        return ambiente

    @staticmethod
    def adicionar_eletrodomestico(ambiente: AmbienteOrcamento, eletro: str) -> AmbienteOrcamento:
        """Adicionar um eletrodoméstico à lista."""
        el = (eletro or "").strip()
        if not el:
            raise ValueError("Eletrodoméstico não pode ser vazio.")
        if el not in ambiente.eletrodomesticos:
            ambiente.eletrodomesticos.append(el)
            ambiente.save(update_fields=["eletrodomesticos", "atualizado_em"])
        return ambiente

    @staticmethod
    def remover_eletrodomestico(ambiente: AmbienteOrcamento, eletro: str) -> AmbienteOrcamento:
        """Remover um eletrodoméstico da lista."""
        el = (eletro or "").strip()
        if el in ambiente.eletrodomesticos:
            ambiente.eletrodomesticos.remove(el)
            ambiente.save(update_fields=["eletrodomesticos", "atualizado_em"])
        return ambiente

    @staticmethod
    def atualizar_observacoes_especiais(ambiente: AmbienteOrcamento, schema: AmbienteDetalhesInputSchema) -> AmbienteOrcamento:
        """Atualizar observações especiais."""
        ambiente.observacoes_especiais = schema.observacoes_especiais
        ambiente.save(update_fields=["observacoes_especiais", "atualizado_em"])
        return ambiente

    @staticmethod
    @transaction.atomic
    def remover_ambiente(ambiente: AmbienteOrcamento) -> None:
        ambiente.delete()

    @staticmethod
    @transaction.atomic
    def excluir_cliente_completo(cliente: ClienteComercial) -> None:
        api = DinaboxAPIClient()
        try:
            api.delete_customer(cliente.customer_id)
        except DinaboxRequestError as exc:
            raise ValueError(f"Falha ao excluir cliente na Dinabox: {exc}") from exc
        cliente.delete()
