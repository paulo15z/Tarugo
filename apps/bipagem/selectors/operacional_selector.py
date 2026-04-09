from __future__ import annotations

from django.db.models import Sum
from django.db.models import Q

from apps.bipagem.domain.operacional import (
    ETAPAS_PREENCHIMENTO_MODULO,
    EtapaOperacional,
    MovimentoOperacional,
    parse_roteiro_operacional,
)
from apps.bipagem.models import EnvioExpedicao, EventoOperacional
from apps.pcp.models import PecaPCP


def list_grupos_expedicao(pid: str, ambiente: str = "") -> list[dict]:
    qs = (
        PecaPCP.objects
        .filter(modulo__ambiente__lote__pid=pid)
        .select_related("modulo__ambiente__lote")
        .order_by("modulo__ambiente__nome", "modulo__nome", "codigo_peca")
    )
    if ambiente:
        qs = qs.filter(modulo__ambiente__nome__iexact=ambiente)

    grupos: dict[tuple[str, str, str], dict] = {}
    pecas = list(qs)
    separados_map = {
        item["peca_id"]: int(item["total"] or 0)
        for item in (
            EventoOperacional.objects
            .filter(
                lote_pid=pid,
                etapa=EtapaOperacional.SEPARACAO_DESTINOS,
                movimento=MovimentoOperacional.BIPAGEM,
                peca_id__in=[peca.id for peca in pecas],
            )
            .values("peca_id")
            .annotate(total=Sum("quantidade"))
        )
    }

    for peca in pecas:
        ambiente_nome = peca.modulo.ambiente.nome if peca.modulo and peca.modulo.ambiente else ""
        modulo_nome = peca.modulo.nome if peca.modulo else ""
        codigo_modulo = peca.codigo_modulo or (peca.modulo.codigo_modulo if peca.modulo else "") or ""
        chave = (ambiente_nome, codigo_modulo, modulo_nome)
        if chave not in grupos:
            grupos[chave] = {
                "lote_pid": pid,
                "cliente_nome": peca.modulo.ambiente.lote.cliente_nome if peca.modulo and peca.modulo.ambiente else "",
                "ambiente": ambiente_nome,
                "modulo": modulo_nome,
                "codigo_modulo": codigo_modulo,
                "total_pecas": 0,
                "total_unidades": 0,
                "total_separado": 0,
                "destinos": set(),
                "pecas": [],
            }

        grupo = grupos[chave]
        grupo["total_pecas"] += 1
        grupo["total_unidades"] += int(peca.quantidade_planejada or 0)
        grupo["total_separado"] += min(separados_map.get(peca.id, 0), int(peca.quantidade_planejada or 0))
        if peca.plano:
            grupo["destinos"].add(peca.plano)
        grupo["pecas"].append({
            "peca_id": str(peca.id),
            "codigo_peca": peca.codigo_peca,
            "descricao": peca.descricao,
            "quantidade_planejada": peca.quantidade_planejada,
            "quantidade_separada": min(separados_map.get(peca.id, 0), int(peca.quantidade_planejada or 0)),
            "destino": peca.plano or "",
        })

    resultado = []
    for grupo in grupos.values():
        grupo["destinos"] = sorted(grupo["destinos"])
        grupo["separacao_concluida"] = grupo["total_unidades"] > 0 and grupo["total_separado"] >= grupo["total_unidades"]
        resultado.append(grupo)

    return sorted(resultado, key=lambda item: (item["ambiente"], item["modulo"], item["codigo_modulo"]))


def list_envios_expedicao(status: str = "") -> list[dict]:
    qs = EnvioExpedicao.objects.all().prefetch_related("itens")
    if status:
        qs = qs.filter(status=status)

    return [
        {
            "codigo": envio.codigo,
            "descricao": envio.descricao,
            "status": envio.status,
            "transportadora": envio.transportadora,
            "placa_veiculo": envio.placa_veiculo,
            "motorista": envio.motorista,
            "ajudante": envio.ajudante,
            "destino_principal": envio.destino_principal,
            "destinos_secundarios": envio.destinos_secundarios,
            "recebido_em": envio.recebido_em.isoformat() if envio.recebido_em else None,
            "liberado_em": envio.liberado_em.isoformat() if envio.liberado_em else None,
            "total_itens": envio.itens.count(),
            "total_unidades": sum(item.quantidade for item in envio.itens.all()),
        }
        for envio in qs
    ]


def get_envio_expedicao(codigo: str) -> dict | None:
    envio = (
        EnvioExpedicao.objects
        .filter(codigo=codigo)
        .prefetch_related("itens__peca__modulo__ambiente__lote")
        .first()
    )
    if not envio:
        return None

    itens = [
        {
            "peca_id": str(item.peca_id),
            "codigo_peca": item.peca.codigo_peca,
            "descricao": item.peca.descricao,
            "quantidade": item.quantidade,
            "lote_pid": item.lote_pid,
            "cliente_nome": item.cliente_nome,
            "ambiente": item.ambiente_nome,
            "modulo": item.modulo_nome,
            "codigo_modulo": item.codigo_modulo,
        }
        for item in envio.itens.all()
    ]
    clientes = sorted({item["cliente_nome"] for item in itens if item["cliente_nome"]})
    lotes = sorted({item["lote_pid"] for item in itens if item["lote_pid"]})

    return {
        "codigo": envio.codigo,
        "descricao": envio.descricao,
        "status": envio.status,
        "transportadora": envio.transportadora,
        "placa_veiculo": envio.placa_veiculo,
        "motorista": envio.motorista,
        "ajudante": envio.ajudante,
        "destino_principal": envio.destino_principal,
        "destinos_secundarios": envio.destinos_secundarios,
        "observacoes": envio.observacoes,
        "recebido_em": envio.recebido_em.isoformat() if envio.recebido_em else None,
        "liberado_em": envio.liberado_em.isoformat() if envio.liberado_em else None,
        "clientes": clientes,
        "lotes": lotes,
        "itens": itens,
        "total_itens": len(itens),
        "total_unidades": sum(item["quantidade"] for item in itens),
    }


def list_viagens_por_lote(pid: str) -> list[dict]:
    return [envio for envio in list_envios_expedicao() if pid in get_envio_expedicao(envio["codigo"]).get("lotes", [])]


def get_resumo_operacional(pid: str) -> dict:
    eventos = EventoOperacional.objects.filter(lote_pid=pid)
    return {
        "lote_pid": pid,
        "separacao_destinos": {
            "total_eventos": eventos.filter(etapa=EtapaOperacional.SEPARACAO_DESTINOS).count(),
            "total_unidades": eventos.filter(
                etapa=EtapaOperacional.SEPARACAO_DESTINOS,
                movimento=MovimentoOperacional.BIPAGEM,
            ).aggregate(total=Sum("quantidade"))["total"] or 0,
        },
        "expedicao": {
            "total_entradas": eventos.filter(
                etapa=EtapaOperacional.EXPEDICAO,
                movimento=MovimentoOperacional.ENTRADA,
            ).count(),
            "total_saidas": eventos.filter(
                etapa=EtapaOperacional.EXPEDICAO,
                movimento=MovimentoOperacional.SAIDA,
            ).count(),
        },
    }


def list_auditoria_pecas(pid: str, ambiente: str = "", modulo: str = "") -> list[dict]:
    qs = (
        PecaPCP.objects
        .filter(modulo__ambiente__lote__pid=pid)
        .select_related("modulo__ambiente__lote")
        .order_by("modulo__ambiente__nome", "modulo__nome", "codigo_peca")
    )
    if ambiente:
        qs = qs.filter(modulo__ambiente__nome__iexact=ambiente)
    if modulo:
        qs = qs.filter(Q(modulo__codigo_modulo__iexact=modulo) | Q(codigo_modulo__iexact=modulo))

    pecas = list(qs)
    eventos = _eventos_bipados_por_peca(pecas)

    resultado: list[dict] = []
    for peca in pecas:
        etapas_roteiro = parse_roteiro_operacional(peca.roteiro)
        etapas_info = []
        etapa_atual = None
        proxima_etapa = None
        for etapa in etapas_roteiro:
            quantidade = _quantidade_evento(eventos, peca.id, etapa)
            concluida = quantidade >= int(peca.quantidade_planejada or 0)
            if not concluida and proxima_etapa is None:
                proxima_etapa = etapa.value
            if concluida:
                etapa_atual = etapa.value
            etapas_info.append({
                "etapa": etapa.value,
                "label": etapa.label,
                "quantidade_concluida": quantidade,
                "quantidade_planejada": int(peca.quantidade_planejada or 0),
                "concluida": concluida,
            })

        resultado.append({
            "peca_id": str(peca.id),
            "codigo_peca": peca.codigo_peca,
            "descricao": peca.descricao,
            "cliente_nome": peca.modulo.ambiente.lote.cliente_nome if peca.modulo and peca.modulo.ambiente else "",
            "lote_pid": peca.modulo.ambiente.lote.pid if peca.modulo and peca.modulo.ambiente else "",
            "ambiente": peca.modulo.ambiente.nome if peca.modulo and peca.modulo.ambiente else "",
            "modulo": peca.modulo.nome if peca.modulo else "",
            "codigo_modulo": peca.codigo_modulo or (peca.modulo.codigo_modulo if peca.modulo else "") or "",
            "quantidade_planejada": int(peca.quantidade_planejada or 0),
            "etapa_atual": etapa_atual,
            "proxima_etapa": proxima_etapa,
            "etapas": etapas_info,
            "aguardando_preenchimento_modulo": proxima_etapa in {etapa.value for etapa in ETAPAS_PREENCHIMENTO_MODULO},
        })
    return resultado


def list_modulos_preenchimento(pid: str, ambiente: str = "") -> list[dict]:
    qs = (
        PecaPCP.objects
        .filter(modulo__ambiente__lote__pid=pid)
        .select_related("modulo__ambiente__lote")
        .order_by("modulo__ambiente__nome", "modulo__nome", "codigo_peca")
    )
    if ambiente:
        qs = qs.filter(modulo__ambiente__nome__iexact=ambiente)

    pecas = list(qs)
    eventos = _eventos_bipados_por_peca(pecas)
    grupos: dict[tuple[str, str, str], dict] = {}

    for peca in pecas:
        ambiente_nome = peca.modulo.ambiente.nome if peca.modulo and peca.modulo.ambiente else ""
        modulo_nome = peca.modulo.nome if peca.modulo else ""
        codigo_modulo = peca.codigo_modulo or (peca.modulo.codigo_modulo if peca.modulo else "") or ""
        chave = (ambiente_nome, codigo_modulo, modulo_nome)
        grupo = grupos.setdefault(chave, {
            "lote_pid": pid,
            "cliente_nome": peca.modulo.ambiente.lote.cliente_nome if peca.modulo and peca.modulo.ambiente else "",
            "ambiente": ambiente_nome,
            "modulo": modulo_nome,
            "codigo_modulo": codigo_modulo,
            "setores": {},
            "pecas_mortas": [],
        })

        etapas_roteiro = parse_roteiro_operacional(peca.roteiro)
        proxima = None
        for etapa in etapas_roteiro:
            if _quantidade_evento(eventos, peca.id, etapa) < int(peca.quantidade_planejada or 0):
                proxima = etapa
                break

        if proxima is None:
            continue

        if proxima in ETAPAS_PREENCHIMENTO_MODULO:
            grupo_setor = grupo["setores"].setdefault(proxima.value, _novo_status_setor(proxima))
            grupo_setor["pecas_prontas"].append(_resumo_peca(peca))
            grupo_setor["prontas"] += 1

        for etapa in etapas_roteiro:
            if etapa not in ETAPAS_PREENCHIMENTO_MODULO:
                continue
            grupo_setor = grupo["setores"].setdefault(etapa.value, _novo_status_setor(etapa))
            grupo_setor["total_previstas"] += 1
            quantidade_concluida = _quantidade_evento(eventos, peca.id, etapa)
            if quantidade_concluida >= int(peca.quantidade_planejada or 0):
                grupo_setor["concluidas"] += 1
            elif _peca_pronta_para_setor(peca, etapa, eventos):
                grupo_setor["liberadas"] += 1
            else:
                grupo_setor["pendentes"] += 1
                grupo_setor["pecas_pendentes"].append({
                    **_resumo_peca(peca),
                    "pendencias": _pendencias_antes_do_setor(peca, etapa, eventos),
                })

        if proxima not in ETAPAS_PREENCHIMENTO_MODULO and not any(etapa in ETAPAS_PREENCHIMENTO_MODULO for etapa in etapas_roteiro):
            grupo["pecas_mortas"].append({
                **_resumo_peca(peca),
                "proxima_etapa": proxima.value if proxima else None,
            })

    resultado = []
    for grupo in grupos.values():
        for setor in grupo["setores"].values():
            setor["status"] = _status_setor(setor)
        grupo["setores"] = sorted(grupo["setores"].values(), key=lambda item: item["ordem"])
        resultado.append(grupo)

    return sorted(resultado, key=lambda item: (item["ambiente"], item["modulo"], item["codigo_modulo"]))


def _eventos_bipados_por_peca(pecas: list[PecaPCP]) -> dict[tuple[object, str], int]:
    if not pecas:
        return {}
    agregados = (
        EventoOperacional.objects
        .filter(
            peca_id__in=[peca.id for peca in pecas],
            movimento=MovimentoOperacional.BIPAGEM,
        )
        .values("peca_id", "etapa")
        .annotate(total=Sum("quantidade"))
    )
    return {(item["peca_id"], item["etapa"]): int(item["total"] or 0) for item in agregados}


def _quantidade_evento(eventos: dict[tuple[object, str], int], peca_id, etapa: EtapaOperacional) -> int:
    return eventos.get((peca_id, etapa.value), 0)


def _pendencias_antes_do_setor(peca: PecaPCP, etapa: EtapaOperacional, eventos: dict[tuple[object, str], int]) -> list[str]:
    etapas_roteiro = parse_roteiro_operacional(peca.roteiro)
    if etapa not in etapas_roteiro:
        return []
    pendencias = []
    for etapa_anterior in etapas_roteiro[:etapas_roteiro.index(etapa)]:
        if etapa_anterior in ETAPAS_PREENCHIMENTO_MODULO:
            continue
        if _quantidade_evento(eventos, peca.id, etapa_anterior) < int(peca.quantidade_planejada or 0):
            pendencias.append(etapa_anterior.label)
    return pendencias


def _peca_pronta_para_setor(peca: PecaPCP, etapa: EtapaOperacional, eventos: dict[tuple[object, str], int]) -> bool:
    return len(_pendencias_antes_do_setor(peca, etapa, eventos)) == 0


def _novo_status_setor(etapa: EtapaOperacional) -> dict:
    return {
        "setor": etapa.value,
        "label": etapa.label,
        "ordem": list(EtapaOperacional).index(etapa),
        "total_previstas": 0,
        "prontas": 0,
        "liberadas": 0,
        "concluidas": 0,
        "pendentes": 0,
        "pecas_prontas": [],
        "pecas_pendentes": [],
    }


def _status_setor(setor: dict) -> str:
    total = setor["total_previstas"]
    if total == 0:
        return "nao_aplicavel"
    if setor["concluidas"] >= total:
        return "concluido"
    if setor["liberadas"] >= total:
        return "liberado"
    if setor["concluidas"] > 0 or setor["liberadas"] > 0 or setor["prontas"] > 0:
        return "parcial"
    return "aguardando"


def _resumo_peca(peca: PecaPCP) -> dict:
    return {
        "peca_id": str(peca.id),
        "codigo_peca": peca.codigo_peca,
        "descricao": peca.descricao,
        "quantidade_planejada": int(peca.quantidade_planejada or 0),
    }
