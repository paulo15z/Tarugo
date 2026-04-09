from __future__ import annotations

from uuid import uuid4

from django.db import transaction
from django.db.models import Sum
from django.db.models import Q
from django.utils import timezone
from pydantic import ValidationError as PydanticValidationError

from apps.bipagem.domain.operacional import (
    EscopoOperacional,
    ETAPAS_PREENCHIMENTO_MODULO,
    EtapaOperacional,
    MovimentoOperacional,
    StatusEnvioExpedicao,
    parse_roteiro_operacional,
)
from apps.bipagem.models import EnvioExpedicao, EnvioExpedicaoItem, EventoOperacional
from apps.bipagem.schemas.operacional_ext_schema import (
    EnvioExpedicaoAddItemInput,
    EnvioExpedicaoAddModuloInput,
    EnvioExpedicaoCreateInput,
    EnvioExpedicaoMovimentoInput,
    EventoPecaInput,
    SeparacaoDestinoInput,
)
from apps.bipagem.selectors.operacional_selector import get_envio_expedicao
from apps.pcp.models import PecaPCP
from apps.pcp.services.pcp_interface import _processamento_liberado_para_bipagem, _resolver_peca_por_codigo


def _erro_validacao(exc: Exception) -> dict[str, object]:
    return {
        "sucesso": False,
        "mensagem": "Dados de entrada invalidos.",
        "erro": str(exc),
    }


def _snapshot_peca(peca) -> dict[str, str]:
    return {
        "lote_pid": peca.modulo.ambiente.lote.pid if peca.modulo and peca.modulo.ambiente else "",
        "cliente_nome": peca.modulo.ambiente.lote.cliente_nome if peca.modulo and peca.modulo.ambiente else "",
        "ambiente_nome": peca.modulo.ambiente.nome if peca.modulo and peca.modulo.ambiente else "",
        "modulo_nome": peca.modulo.nome if peca.modulo else "",
        "codigo_modulo": peca.codigo_modulo or (peca.modulo.codigo_modulo if peca.modulo else "") or "",
    }


def _gerar_codigo_envio() -> str:
    return f"ENV-{uuid4().hex[:8].upper()}"


def _registrar_evento_peca(
    *,
    peca,
    etapa: EtapaOperacional,
    quantidade: int,
    usuario: str,
    localizacao: str,
    observacao: str = "",
    movimento: MovimentoOperacional = MovimentoOperacional.BIPAGEM,
) -> EventoOperacional:
    snapshot = _snapshot_peca(peca)
    return EventoOperacional.objects.create(
        etapa=etapa,
        movimento=movimento,
        escopo=EscopoOperacional.PECA_PCP,
        peca=peca,
        quantidade=quantidade,
        usuario=usuario,
        localizacao=localizacao,
        lote_pid=snapshot["lote_pid"],
        codigo_modulo=snapshot["codigo_modulo"],
        ambiente_nome=snapshot["ambiente_nome"],
        destino=peca.plano or "",
        observacao=observacao or (peca.roteiro or ""),
    )


def _total_eventos_peca(peca, etapa: EtapaOperacional) -> int:
    total = (
        EventoOperacional.objects
        .filter(
            peca=peca,
            etapa=etapa,
            movimento=MovimentoOperacional.BIPAGEM,
        )
        .aggregate(total=Sum("quantidade"))["total"]
    )
    return int(total or 0)


@transaction.atomic
def registrar_evento_peca(data: dict) -> dict[str, object]:
    try:
        payload = EventoPecaInput(**data)
    except PydanticValidationError as exc:
        return _erro_validacao(exc)

    if not payload.etapa_auditavel:
        return {"sucesso": False, "mensagem": "Etapa nao suportada para auditoria por peca."}
    if not _processamento_liberado_para_bipagem(payload.pid):
        return {"sucesso": False, "mensagem": "Lote bloqueado ou nao liberado para bipagem."}

    peca, erro_resolucao = _resolver_peca_por_codigo(payload.pid, payload.codigo_peca)
    if erro_resolucao:
        return {"sucesso": False, "mensagem": erro_resolucao}

    etapas_roteiro = parse_roteiro_operacional(peca.roteiro)
    if payload.etapa not in etapas_roteiro and payload.etapa not in {
        EtapaOperacional.RECEBIMENTO_ITEM,
        EtapaOperacional.SEPARACAO_RESERVA,
        EtapaOperacional.SEPARACAO_DESTINOS,
    }:
        return {"sucesso": False, "mensagem": "Etapa nao prevista no roteiro desta peca."}

    if payload.etapa in ETAPAS_PREENCHIMENTO_MODULO:
        etapas_anteriores = [etapa for etapa in etapas_roteiro[:etapas_roteiro.index(payload.etapa)] if etapa not in ETAPAS_PREENCHIMENTO_MODULO]
        pendentes = [etapa.label for etapa in etapas_anteriores if _total_eventos_peca(peca, etapa) < int(peca.quantidade_planejada or 0)]
        if pendentes:
            return {
                "sucesso": False,
                "mensagem": "Peca ainda nao esta pronta para este setor.",
                "pendencias": pendentes,
            }

    total_ja_registrado = _total_eventos_peca(peca, payload.etapa)
    faltam = max(int(peca.quantidade_planejada or 0) - total_ja_registrado, 0)
    if faltam <= 0:
        return {
            "sucesso": True,
            "repetido": True,
            "mensagem": "Etapa ja registrada anteriormente para esta peca.",
            "peca": _build_peca_output(peca, total_ja_registrado),
            "etapa": payload.etapa.value,
        }

    quantidade_aplicada = min(payload.quantidade, faltam)
    _registrar_evento_peca(
        peca=peca,
        etapa=payload.etapa,
        quantidade=quantidade_aplicada,
        usuario=payload.usuario,
        localizacao=payload.localizacao or payload.etapa.value,
        observacao=payload.observacao,
    )
    return {
        "sucesso": True,
        "repetido": False,
        "mensagem": "Etapa registrada com sucesso para a peca.",
        "peca": _build_peca_output(peca, total_ja_registrado + quantidade_aplicada),
        "etapa": payload.etapa.value,
    }


@transaction.atomic
def registrar_separacao_destino(data: dict) -> dict[str, object]:
    try:
        payload = SeparacaoDestinoInput(**data)
    except PydanticValidationError as exc:
        return _erro_validacao(exc)

    if not _processamento_liberado_para_bipagem(payload.pid):
        return {"sucesso": False, "mensagem": "Lote bloqueado ou nao liberado para bipagem."}

    peca, erro_resolucao = _resolver_peca_por_codigo(payload.pid, payload.codigo_peca)
    if erro_resolucao:
        return {"sucesso": False, "mensagem": erro_resolucao}

    total_ja_registrado = _total_eventos_peca(peca, EtapaOperacional.SEPARACAO_DESTINOS)
    faltam = max(int(peca.quantidade_planejada or 0) - total_ja_registrado, 0)
    if faltam <= 0:
        return {
            "sucesso": True,
            "repetido": True,
            "mensagem": "Peca ja separada para destino anteriormente.",
            "peca": _build_peca_output(peca, total_ja_registrado),
        }

    quantidade_aplicada = min(payload.quantidade, faltam)
    evento = _registrar_evento_peca(
        peca=peca,
        etapa=EtapaOperacional.SEPARACAO_DESTINOS,
        quantidade=quantidade_aplicada,
        usuario=payload.usuario,
        localizacao=payload.localizacao,
    )
    _ = evento

    return {
        "sucesso": True,
        "repetido": False,
        "mensagem": "Separacao de destino registrada com sucesso.",
        "peca": _build_peca_output(peca, total_ja_registrado + quantidade_aplicada),
    }


@transaction.atomic
def criar_envio_expedicao(data: dict) -> dict[str, object]:
    try:
        payload = EnvioExpedicaoCreateInput(**data)
    except PydanticValidationError as exc:
        return _erro_validacao(exc)

    codigo = (payload.codigo or "").strip().upper() or _gerar_codigo_envio()
    if EnvioExpedicao.objects.filter(codigo=codigo).exists():
        return {"sucesso": False, "mensagem": "Ja existe um envio com este codigo."}

    envio = EnvioExpedicao.objects.create(
        codigo=codigo,
        descricao=payload.descricao.strip(),
        transportadora=payload.transportadora.strip(),
        placa_veiculo=payload.placa_veiculo.strip().upper(),
        motorista=payload.motorista.strip(),
        ajudante=payload.ajudante.strip(),
        destino_principal=payload.destino_principal.strip(),
        destinos_secundarios=[item.strip() for item in payload.destinos_secundarios if item.strip()],
        observacoes=payload.observacoes.strip(),
        criado_por=payload.usuario,
        atualizado_por=payload.usuario,
    )
    return {
        "sucesso": True,
        "mensagem": "Envio criado com sucesso.",
        "envio": get_envio_expedicao(envio.codigo),
    }


@transaction.atomic
def adicionar_item_envio(data: dict) -> dict[str, object]:
    try:
        payload = EnvioExpedicaoAddItemInput(**data)
    except PydanticValidationError as exc:
        return _erro_validacao(exc)

    envio = EnvioExpedicao.objects.filter(codigo=payload.envio_codigo).first()
    if not envio:
        return {"sucesso": False, "mensagem": "Envio nao encontrado."}
    if envio.status == StatusEnvioExpedicao.LIBERADO:
        return {"sucesso": False, "mensagem": "Nao e possivel alterar um envio ja liberado."}
    if not _processamento_liberado_para_bipagem(payload.pid):
        return {"sucesso": False, "mensagem": "Lote bloqueado ou nao liberado para bipagem."}

    peca, erro_resolucao = _resolver_peca_por_codigo(payload.pid, payload.codigo_peca)
    if erro_resolucao:
        return {"sucesso": False, "mensagem": erro_resolucao}

    snapshot = _snapshot_peca(peca)
    item, created = EnvioExpedicaoItem.objects.get_or_create(
        envio=envio,
        peca=peca,
        defaults={
            "quantidade": min(payload.quantidade, int(peca.quantidade_planejada or 0)),
            "lote_pid": snapshot["lote_pid"],
            "cliente_nome": snapshot["cliente_nome"],
            "ambiente_nome": snapshot["ambiente_nome"],
            "modulo_nome": snapshot["modulo_nome"],
            "codigo_modulo": snapshot["codigo_modulo"],
            "criado_por": payload.usuario,
            "atualizado_por": payload.usuario,
        },
    )
    if not created:
        limite = int(peca.quantidade_planejada or 0)
        item.quantidade = min(item.quantidade + payload.quantidade, limite)
        item.atualizado_por = payload.usuario
        item.save(update_fields=["quantidade", "atualizado_por", "atualizado_em"])

    return {
        "sucesso": True,
        "mensagem": "Item vinculado ao envio com sucesso.",
        "envio": get_envio_expedicao(envio.codigo),
    }


@transaction.atomic
def adicionar_modulo_envio(data: dict) -> dict[str, object]:
    try:
        payload = EnvioExpedicaoAddModuloInput(**data)
    except PydanticValidationError as exc:
        return _erro_validacao(exc)

    envio = EnvioExpedicao.objects.filter(codigo=payload.envio_codigo).first()
    if not envio:
        return {"sucesso": False, "mensagem": "Viagem nao encontrada."}
    if envio.status == StatusEnvioExpedicao.LIBERADO:
        return {"sucesso": False, "mensagem": "Nao e possivel alterar uma viagem ja liberada."}
    if not _processamento_liberado_para_bipagem(payload.pid):
        return {"sucesso": False, "mensagem": "Lote bloqueado ou nao liberado para bipagem."}

    pecas_qs = (
        PecaPCP.objects
        .filter(modulo__ambiente__lote__pid=payload.pid)
        .select_related("modulo__ambiente__lote")
    )
    if payload.ambiente:
        pecas_qs = pecas_qs.filter(modulo__ambiente__nome__iexact=payload.ambiente)
    pecas_qs = pecas_qs.filter(
        Q(codigo_modulo__iexact=payload.codigo_modulo) |
        Q(modulo__codigo_modulo__iexact=payload.codigo_modulo)
    )
    pecas = list(pecas_qs)
    if not pecas:
        return {"sucesso": False, "mensagem": "Modulo nao encontrado neste lote."}

    adicionadas = 0
    for peca in pecas:
        snapshot = _snapshot_peca(peca)
        _, created = EnvioExpedicaoItem.objects.get_or_create(
            envio=envio,
            peca=peca,
            defaults={
                "quantidade": int(peca.quantidade_planejada or 0),
                "lote_pid": snapshot["lote_pid"],
                "cliente_nome": snapshot["cliente_nome"],
                "ambiente_nome": snapshot["ambiente_nome"],
                "modulo_nome": snapshot["modulo_nome"],
                "codigo_modulo": snapshot["codigo_modulo"],
                "criado_por": payload.usuario,
                "atualizado_por": payload.usuario,
            },
        )
        if created:
            adicionadas += 1

    return {
        "sucesso": True,
        "mensagem": f"Modulo vinculado a viagem com {adicionadas} peca(s) nova(s).",
        "envio": get_envio_expedicao(envio.codigo),
    }


@transaction.atomic
def registrar_entrada_expedicao(data: dict) -> dict[str, object]:
    return _registrar_movimento_envio(data=data, movimento=MovimentoOperacional.ENTRADA)


@transaction.atomic
def registrar_saida_expedicao(data: dict) -> dict[str, object]:
    return _registrar_movimento_envio(data=data, movimento=MovimentoOperacional.SAIDA)


def _registrar_movimento_envio(data: dict, movimento: MovimentoOperacional) -> dict[str, object]:
    try:
        payload = EnvioExpedicaoMovimentoInput(**data)
    except PydanticValidationError as exc:
        return _erro_validacao(exc)

    envio = (
        EnvioExpedicao.objects
        .filter(codigo=payload.envio_codigo)
        .prefetch_related("itens__peca")
        .first()
    )
    if not envio:
        return {"sucesso": False, "mensagem": "Envio nao encontrado."}
    if not envio.itens.exists():
        return {"sucesso": False, "mensagem": "Envio sem itens nao pode receber movimentacao."}
    if movimento == MovimentoOperacional.ENTRADA and envio.status != StatusEnvioExpedicao.ABERTO:
        return {"sucesso": False, "mensagem": "Somente envios abertos podem registrar entrada."}
    if movimento == MovimentoOperacional.SAIDA and envio.status != StatusEnvioExpedicao.RECEBIDO:
        return {"sucesso": False, "mensagem": "Somente envios recebidos podem registrar liberacao."}

    for item in envio.itens.all():
        evento_ja_existe = EventoOperacional.objects.filter(
            etapa=EtapaOperacional.EXPEDICAO,
            movimento=movimento,
            envio=envio,
            peca=item.peca,
        ).exists()
        if evento_ja_existe:
            continue

        EventoOperacional.objects.create(
            etapa=EtapaOperacional.EXPEDICAO,
            movimento=movimento,
            escopo=EscopoOperacional.PECA_PCP,
            envio=envio,
            peca=item.peca,
            quantidade=item.quantidade,
            usuario=payload.usuario,
            localizacao=payload.localizacao,
            lote_pid=item.lote_pid,
            codigo_modulo=item.codigo_modulo,
            ambiente_nome=item.ambiente_nome,
            destino="ENVIO",
            observacao=payload.observacao,
        )

    now = timezone.now()
    if movimento == MovimentoOperacional.ENTRADA:
        envio.status = StatusEnvioExpedicao.RECEBIDO
        envio.recebido_em = now
        envio.atualizado_por = payload.usuario
        envio.save(update_fields=["status", "recebido_em", "atualizado_por", "atualizado_em"])
        mensagem = "Entrada na expedicao registrada com sucesso."
    else:
        envio.status = StatusEnvioExpedicao.LIBERADO
        envio.liberado_em = now
        envio.atualizado_por = payload.usuario
        envio.save(update_fields=["status", "liberado_em", "atualizado_por", "atualizado_em"])
        mensagem = "Saida da expedicao registrada com sucesso."

    return {
        "sucesso": True,
        "mensagem": mensagem,
        "envio": get_envio_expedicao(envio.codigo),
    }


def _build_peca_output(peca, quantidade_separada: int) -> dict[str, object]:
    snapshot = _snapshot_peca(peca)
    return {
        "peca_id": str(peca.id),
        "codigo_peca": peca.codigo_peca,
        "descricao": peca.descricao,
        "quantidade_planejada": int(peca.quantidade_planejada or 0),
        "quantidade_separada": quantidade_separada,
        "ambiente": snapshot["ambiente_nome"],
        "modulo": snapshot["modulo_nome"],
        "codigo_modulo": snapshot["codigo_modulo"],
        "destino": peca.plano or "",
        "roteiro": peca.roteiro or "",
    }
