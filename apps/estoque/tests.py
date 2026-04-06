from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.estoque.models import CategoriaProduto, Produto
from apps.estoque.selectors.disponibilidade_selector import get_saldo_disponivel, get_saldo_fisico
from apps.estoque.services.reserva_service import ReservaService


class ReservaIndustrialTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="123456")
        self.categoria = CategoriaProduto.objects.create(nome="Ferragens", familia="ferragens")
        self.produto = Produto.objects.create(
            nome="Parafuso 5x50",
            sku="PAR-5X50",
            categoria=self.categoria,
            quantidade=10,
            estoque_minimo=2,
            unidade_medida="un",
        )

    def test_reserva_reduz_disponibilidade_sem_reduzir_fisico(self):
        ReservaService.criar_reserva(
            {
                "produto_id": self.produto.id,
                "quantidade": 4,
                "referencia_externa": "PED-001",
                "origem_externa": "pcp",
            },
            usuario=self.user,
        )

        self.produto.refresh_from_db()
        self.assertEqual(get_saldo_fisico(self.produto), 10)
        self.assertEqual(get_saldo_disponivel(self.produto), 6)

    def test_cancelar_reserva_recompoe_disponibilidade(self):
        reserva = ReservaService.criar_reserva(
            {
                "produto_id": self.produto.id,
                "quantidade": 3,
                "referencia_externa": "PED-002",
                "origem_externa": "pcp",
            },
            usuario=self.user,
        )

        ReservaService.cancelar_reserva(reserva.id, usuario=self.user)
        self.assertEqual(get_saldo_disponivel(self.produto), 10)

    def test_consumir_reserva_baixa_fisico_e_conclui_reserva(self):
        reserva = ReservaService.criar_reserva(
            {
                "produto_id": self.produto.id,
                "quantidade": 2,
                "referencia_externa": "PED-003",
                "origem_externa": "pcp",
            },
            usuario=self.user,
        )

        ReservaService.consumir_reserva(reserva.id, usuario=self.user)

        self.produto.refresh_from_db()
        reserva.refresh_from_db()
        self.assertEqual(reserva.status, "consumida")
        self.assertEqual(self.produto.quantidade, 8)
        self.assertEqual(get_saldo_disponivel(self.produto), 8)
