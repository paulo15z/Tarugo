from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.comercial.models import AmbienteOrcamento, ClienteComercial, StatusClienteComercial
from apps.integracoes.models import DinaboxClienteIndex
from apps.pedidos.domain.status import AmbienteStatus, PedidoStatus
from apps.pedidos.services import PedidoService
from apps.projetos.domain.status import ProjetoStatus
from apps.projetos.models import Projeto
from apps.projetos.services import ProjetoService


class ProjetoServiceTests(TestCase):
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
        AmbienteOrcamento.objects.create(cliente=self.cliente, nome_ambiente="COZINHA", ordem=0)
        AmbienteOrcamento.objects.create(cliente=self.cliente, nome_ambiente="SUITE 1", ordem=1)
        self.pedido = PedidoService.criar_pedido_do_comercial(self.cliente, "573")

    def test_handoff_cria_um_projeto_por_ambiente(self):
        self.assertEqual(Projeto.objects.filter(pedido=self.pedido).count(), 2)
        self.assertTrue(
            Projeto.objects.filter(
                pedido=self.pedido,
                status=ProjetoStatus.AGUARDANDO_DEFINICOES,
            ).count(),
            2,
        )

    def test_liberar_todos_os_projetos_move_pedido_para_macro_seguinte(self):
        projetos = list(Projeto.objects.filter(pedido=self.pedido).order_by("ambiente_pedido__nome_ambiente"))

        ProjetoService.atualizar_status(projetos[0], ProjetoStatus.AGUARDANDO_PROJETISTA)
        ProjetoService.atualizar_status(projetos[0], ProjetoStatus.EM_DESENVOLVIMENTO)
        ProjetoService.atualizar_status(projetos[0], ProjetoStatus.EM_CONFERENCIA)
        ProjetoService.atualizar_status(projetos[0], ProjetoStatus.AGUARDANDO_APROVACAO)
        ProjetoService.atualizar_status(projetos[0], ProjetoStatus.LIBERADO_PARA_PCP)
        self.pedido.refresh_from_db()
        projetos[0].ambiente_pedido.refresh_from_db()

        self.assertEqual(projetos[0].ambiente_pedido.status, AmbienteStatus.AGUARDANDO_PCP)
        self.assertEqual(self.pedido.status, PedidoStatus.ENVIADO_PARA_PROJETOS)

        ProjetoService.atualizar_status(projetos[1], ProjetoStatus.AGUARDANDO_PROJETISTA)
        ProjetoService.atualizar_status(projetos[1], ProjetoStatus.EM_DESENVOLVIMENTO)
        ProjetoService.atualizar_status(projetos[1], ProjetoStatus.EM_CONFERENCIA)
        ProjetoService.atualizar_status(projetos[1], ProjetoStatus.AGUARDANDO_APROVACAO)
        ProjetoService.atualizar_status(projetos[1], ProjetoStatus.LIBERADO_PARA_PCP)
        self.pedido.refresh_from_db()

        self.assertEqual(self.pedido.status, PedidoStatus.EM_ENGENHARIA)


class ProjetoViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="projetista", password="senha123")
        group = self.user.groups.create(name="Projetos_Distribuidor")

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
        AmbienteOrcamento.objects.create(cliente=self.cliente, nome_ambiente="COZINHA", ordem=0)
        self.pedido = PedidoService.criar_pedido_do_comercial(self.cliente, "573")
        self.projeto = Projeto.objects.get(pedido=self.pedido)

    def test_lista_projetos(self):
        self.client.force_login(self.user)
        response = self.client.get("/projetos/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "COZINHA")

    def test_transicao_de_status_via_view(self):
        self.client.force_login(self.user)
        response = self.client.post(f"/projetos/{self.projeto.pk}/status/", {"status": ProjetoStatus.AGUARDANDO_PROJETISTA})
        self.assertEqual(response.status_code, 302)
        self.projeto.refresh_from_db()
        self.assertEqual(self.projeto.status, ProjetoStatus.AGUARDANDO_PROJETISTA)
