from collections import defaultdict
from typing import Any, Dict, List


def parse_project_detail(detail: Any) -> Dict[str, Any]:
    """Normalize a Dinabox project detail payload into a dict with:
    - pecas: list of piece dicts
    - modulos: list of {nome, pecas}
    - cliente: {nome}
    - metadata: basic metadata

    The function is defensive and recognizes several common key names used
    by different Dinabox payloads (woodwork, parts, components, modules, etc.).
    """

    def _get(obj: Any, keys: List[str]):
        for k in keys:
            if isinstance(obj, dict):
                v = obj.get(k)
            else:
                v = getattr(obj, k, None)
            if v not in (None, ""):
                return v
        return None

    def _to_float(val):
        if val is None:
            return None
        try:
            s = str(val).strip()
            if not s:
                return None
            s = s.replace(",", ".")
            return float(s)
        except Exception:
            return None

    def _convert_part(raw: Any, forced_modulo: str | None = None) -> Dict[str, Any]:
        descricao = _get(raw, ["descricao", "description", "part_description", "name", "part", "descricao_peca"]) or ""
        material = _get(raw, ["material", "material_name", "material_description"]) or None

        # dimensoes podem vir em campos separados ou em dict 'dimensoes'
        largura = _to_float(_get(raw, ["largura", "width", "width_mm", "w"]))
        altura = _to_float(_get(raw, ["altura", "height", "height_mm", "h"]))
        # fallback: dimensoes dentro de objeto
        dims = _get(raw, ["dimensoes", "dimensions"])
        if isinstance(dims, dict):
            largura = largura or _to_float(_get(dims, ["largura", "width", "w"]))
            altura = altura or _to_float(_get(dims, ["altura", "height", "h"]))

        espessura = _to_float(_get(raw, ["espessura", "thickness", "thickness_mm", "t"]))

        qtd_raw = _get(raw, ["quantidade", "quantity", "qty", "amount", "count", "qtd"]) or 1
        try:
            quantidade = int(float(str(qtd_raw).replace(",", ".")))
        except Exception:
            quantidade = 1

        modulo = forced_modulo or _get(raw, ["module", "module_name", "descricao_modulo", "modulo", "group"]) or None

        referencia = _get(raw, ["referencia", "reference", "ref", "codigo"]) or None
        if not modulo and isinstance(referencia, str) and " - " in referencia:
            partes = referencia.split(" - ", 1)
            modulo = partes[0].strip()
            if not descricao:
                descricao = partes[1].strip()

        if not modulo:
            modulo = "SEM MODULO"

        return {
            "descricao": descricao,
            "material": material,
            "largura": largura,
            "altura": altura,
            "espessura": espessura,
            "quantidade": quantidade,
            "modulo": modulo,
        }

    # Construir resposta básica
    cliente_nome = _get(detail, ["project_customer_name", "customer_name", "cliente", "client"]) or ""
    metadata = {
        "origem": "dinabox",
        "data_importacao": _get(detail, ["project_created", "created", "date"]) or None,
        "versao": _get(detail, ["project_version", "version"]) or None,
    }

    # 1) Tentar estruturas de módulos explícitos
    module_keys = ["modules", "modulos", "assemblies", "groups", "ambientes", "environments"]
    parts_keys = ["woodwork", "parts", "pieces", "components", "items", "panels", "parts_list"]

    for mk in module_keys:
        modules_val = _get(detail, [mk])
        if isinstance(modules_val, list) and modules_val:
            all_parts = []
            modulos = []
            for m in modules_val:
                nome_mod = _get(m, ["nome", "name", "descricao", "description", "module_name"]) or "SEM MODULO"
                # localizar peças dentro do módulo
                module_parts_raw = None
                for pk in parts_keys + ["parts", "pecas", "components"]:
                    p = _get(m, [pk])
                    if isinstance(p, list):
                        module_parts_raw = p
                        break

                module_parts = []
                if isinstance(module_parts_raw, list):
                    for raw in module_parts_raw:
                        p = _convert_part(raw, forced_modulo=nome_mod)
                        module_parts.append(p)
                        all_parts.append(p)

                modulos.append({"nome": nome_mod, "pecas": module_parts})

            return {"pecas": all_parts, "modulos": modulos, "cliente": {"nome": cliente_nome}, "metadata": metadata}

    # 2) Tentar lista de peças no topo (woodwork, parts, components)
    top_parts = None
    for pk in parts_keys:
        v = _get(detail, [pk])
        if isinstance(v, list) and v:
            top_parts = v
            break

    all_parts = []
    if isinstance(top_parts, list):
        for raw in top_parts:
            # alguns payloads embrulham a peça sob uma chave 'part' ou semelhante
            if isinstance(raw, dict) and len(raw) == 1 and any(k in raw for k in ("part", "peca")):
                inner = next(iter(raw.values()))
            else:
                inner = raw

            p = _convert_part(inner)
            all_parts.append(p)

        # agrupar por modulo
        groups = defaultdict(list)
        for p in all_parts:
            groups[p.get("modulo") or "SEM MODULO"].append(p)

        modulos = [{"nome": k, "pecas": v} for k, v in groups.items()]

        return {"pecas": all_parts, "modulos": modulos, "cliente": {"nome": cliente_nome}, "metadata": metadata}

    # 3) fallback vazio
    return {"pecas": [], "modulos": [], "cliente": {"nome": cliente_nome}, "metadata": metadata}
