from django.test import TestCase

from apps.comercial.models import AmbienteOrcamento, ClienteComercial, StatusClienteComercial
from apps.integracoes.models import DinaboxClienteIndex
from apps.pedidos.domain.status import AmbienteStatus, PedidoStatus
from apps.pedidos.services import PedidoService


class PedidoServiceFromComercialTests(TestCase):
    def setUp(self):
        self.cliente = ClienteComercial.objects.create(
            customer_id="2539544",
            numero_pedido="573",
            status=StatusClienteComercial.CONTRATO_FECHADO,
        )
        DinaboxClienteIndex.objects.create(
            customer_id="2539544",
            customer_name="Cliente MVP",
            customer_type="pf",
            customer_status="on",
        )

        AmbienteOrcamento.objects.create(
            cliente=self.cliente,
            nome_ambiente="COZINHA",
            acabamentos=["MDF"],
            eletrodomesticos=["Forno"],
            observacoes_especiais="Nicho lateral",
            ordem=0,
        )
        AmbienteOrcamento.objects.create(
            cliente=self.cliente,
            nome_ambiente="SALA",
            acabamentos=["Laca"],
            eletrodomesticos=[],
            observacoes_especiais="Painel ripado",
            ordem=1,
        )

    def test_cria_pedido_com_status_de_projetos(self):
        pedido = PedidoService.criar_pedido_do_comercial(self.cliente, self.cliente.numero_pedido)

        self.assertEqual(pedido.numero_pedido, "573")
        self.assertEqual(pedido.status, PedidoStatus.ENVIADO_PARA_PROJETOS)
        self.assertEqual(pedido.cliente_nome, "Cliente MVP")

        ambientes = list(pedido.ambientes.order_by("nome_ambiente"))
        self.assertEqual(len(ambientes), 2)
        self.assertTrue(all(a.status == AmbienteStatus.PENDENTE_PROJETOS for a in ambientes))

    def test_so_move_pedido_para_engenharia_quando_todos_ambientes_chegarem(self):
        pedido = PedidoService.criar_pedido_do_comercial(self.cliente, self.cliente.numero_pedido)
        cozinha = pedido.ambientes.get(nome_ambiente="COZINHA")
        sala = pedido.ambientes.get(nome_ambiente="SALA")

        PedidoService.processar_engenharia_ambiente(cozinha, {"woodwork": []})
        pedido.refresh_from_db()
        cozinha.refresh_from_db()

        self.assertEqual(cozinha.status, AmbienteStatus.AGUARDANDO_PCP)
        self.assertEqual(pedido.status, PedidoStatus.ENVIADO_PARA_PROJETOS)

        PedidoService.processar_engenharia_ambiente(sala, {"woodwork": []})
        pedido.refresh_from_db()

        self.assertEqual(pedido.status, PedidoStatus.EM_ENGENHARIA)
