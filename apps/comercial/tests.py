from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.comercial.models import AmbienteOrcamento, ClienteComercial, StatusClienteComercial
from apps.integracoes.models import DinaboxClienteIndex
from apps.pedidos.domain.status import PedidoStatus
from apps.pedidos.models import Pedido
from apps.projetos.models import Projeto


class ComercialEnviarParaProjetosViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="orcamentista", password="senha123")
        self.user.groups.create(name="comercial_orcamentista")

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
            ordem=0,
        )

    def test_post_envia_para_projetos_e_cria_pedido(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("comercial:enviar_para_projetos_post", args=[self.cliente.pk])
        )

        pedido = Pedido.objects.get(numero_pedido="573")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(pedido.status, PedidoStatus.ENVIADO_PARA_PROJETOS)
        self.assertEqual(response.url, reverse("projetos:pedido-projetos", args=["573"]))
        self.assertEqual(Projeto.objects.filter(pedido=pedido).count(), 1)
