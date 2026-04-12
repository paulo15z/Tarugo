from __future__ import annotations

from typing import Optional

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
