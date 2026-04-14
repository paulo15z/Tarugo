from __future__ import annotations

from typing import Any, Optional

from django.db.models import Prefetch, QuerySet

from apps.integracoes.models import DinaboxClienteIndex

from .models import AmbienteOrcamento, ClienteComercial, ObservacaoComercial


class ComercialSelector:
    @staticmethod
    def list_clientes() -> QuerySet[ClienteComercial]:
        return (
            ClienteComercial.objects.all()
            .select_related("criado_por")
            .order_by("-atualizado_em")
        )

    @staticmethod
    def get_cliente(pk: int) -> Optional[ClienteComercial]:
        return (
            ClienteComercial.objects.filter(pk=pk)
            .select_related("criado_por")
            .prefetch_related(
                Prefetch(
                    "observacoes",
                    queryset=ObservacaoComercial.objects.select_related("autor").order_by("-criado_em"),
                ),
                Prefetch(
                    "ambientes",
                    queryset=AmbienteOrcamento.objects.order_by("ordem", "pk"),
                ),
                "pedidos",
            )
            .first()
        )

    @staticmethod
    def dinabox_index_por_customer_id(customer_id: str) -> Optional[DinaboxClienteIndex]:
        return DinaboxClienteIndex.objects.filter(customer_id=str(customer_id)).first()

    @staticmethod
    def customer_ids_ja_vinculados() -> set[str]:
        return set(ClienteComercial.objects.values_list("customer_id", flat=True))

    @staticmethod
    def candidatos_vinculacao(search: str = "", limit: int = 200) -> QuerySet[DinaboxClienteIndex]:
        """
        Clientes presentes no índice Dinabox ainda sem ficha comercial.
        """
        vinculados = ComercialSelector.customer_ids_ja_vinculados()
        qs = DinaboxClienteIndex.objects.exclude(customer_id__in=vinculados).order_by("customer_name_normalized")
        q = (search or "").strip()
        if q:
            n = DinaboxClienteIndex._normalize(q)
            qs = qs.filter(customer_name_normalized__icontains=n)
        return qs[:limit]

    @staticmethod
    def get_info_para_projetos(cliente_id: int) -> Optional[dict[str, Any]]:
        """
        Retorna estrutura completa do cliente e seus ambientes para consumo por Projetos.
        
        Formato:
        {
            "cliente_id": 123,
            "customer_id": "2539939",
            "nome_cliente": "WAGNER LEMOS",
            "status": "em_orcamento",
            "total_ambientes": 3,
            "valor_total_orcado": 15000.00,
            "ambientes": [
                {
                    "id": 456,
                    "nome": "COZINHA",
                    "valor": 5000.00,
                    "acabamentos": ["Pintura branca", "Piso porcelanato"],
                    "eletrodomesticos": ["Geladeira Brastemp 500L"],
                    "observacoes": "Nicho no fundo da cozinha"
                },
                ...
            ],
            "observacoes_comerciais": [
                {"texto": "Cliente indeciso", "autor": "João", "data": "2026-04-12"}
            ]
        }
        """
        cliente = ComercialSelector.get_cliente(cliente_id)
        if not cliente:
            return None
        
        # Busca índice do cliente para dados essenciais
        idx = ComercialSelector.dinabox_index_por_customer_id(cliente.customer_id)
        
        # Monta estrutura de ambientes
        ambientes = []
        valor_total = 0
        for amb in cliente.ambientes.all():
            valor_amb = float(amb.valor_orcado or 0)
            valor_total += valor_amb
            
            ambientes.append({
                "id": amb.id,
                "nome": amb.nome_ambiente,
                "valor": valor_amb,
                "acabamentos": amb.acabamentos or [],
                "eletrodomesticos": amb.eletrodomesticos or [],
                "observacoes": amb.observacoes_especiais or "",
            })
        
        # Monta observações comerciais
        observacoes = []
        for obs in cliente.observacoes.all():
            observacoes.append({
                "texto": obs.texto,
                "autor": obs.autor.get_full_name() if obs.autor else "Desconhecido",
                "data": obs.criado_em.isoformat(),
            })
        
        return {
            "cliente_id": cliente.id,
            "customer_id": cliente.customer_id,
            "numero_pedido": cliente.numero_pedido,
            "nome_cliente": idx.customer_name if idx else "",
            "status": cliente.get_status_display(),
            "total_ambientes": cliente.ambientes.count(),
            "valor_total_orcado": valor_total,
            "ambientes": ambientes,
            "observacoes_comerciais": observacoes,
            "metadata": {
                "criado_em": cliente.criado_em.isoformat(),
                "atualizado_em": cliente.atualizado_em.isoformat(),
                "criado_por": cliente.criado_por.get_full_name() if cliente.criado_por else "Desconhecido",
            }
        }
