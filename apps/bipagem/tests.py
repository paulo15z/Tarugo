from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.bipagem.domain.operacional import EtapaOperacional, MovimentoOperacional, StatusEnvioExpedicao
from apps.bipagem.models import EnvioExpedicao, EventoOperacional
from apps.bipagem.selectors.operacional_selector import list_auditoria_pecas, list_modulos_preenchimento
from apps.bipagem.services.operacional_service import (
    adicionar_modulo_envio,
    adicionar_item_envio,
    criar_envio_expedicao,
    registrar_evento_peca,
    registrar_entrada_expedicao,
    registrar_saida_expedicao,
    registrar_separacao_destino,
)
from apps.pcp.models import AmbientePCP, LotePCP, ModuloPCP, PecaPCP, ProcessamentoPCP


class OperacionalExpedicaoServiceTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="operador", password="123456")
        self.pid = "ABCD1234"
        self.processamento = ProcessamentoPCP.objects.create(
            id=self.pid,
            nome_arquivo="teste.xls",
            lote=101,
            total_pecas=2,
            liberado_para_bipagem=True,
        )
        self.lote = LotePCP.objects.create(
            pid=self.pid,
            arquivo_original="teste.xls",
            cliente_nome="Cliente Teste",
            cliente_id_projeto="P-001",
            ordem_producao="OP-01",
        )
        self.ambiente = AmbientePCP.objects.create(lote=self.lote, nome="COZINHA")
        self.modulo = ModuloPCP.objects.create(
            ambiente=self.ambiente,
            nome="NICHO AEREO",
            codigo_modulo="M1001",
        )
        self.peca = PecaPCP.objects.create(
            modulo=self.modulo,
            referencia_bruta="M1001 - P001",
            codigo_modulo="M1001",
            codigo_peca="P001",
            descricao="Lateral esquerda",
            quantidade_planejada=1,
            plano="10",
            roteiro="COR > BOR > MAR > CQL > EXP",
        )
        self.peca_gaveta = PecaPCP.objects.create(
            modulo=self.modulo,
            referencia_bruta="M1001 - P002",
            codigo_modulo="M1001",
            codigo_peca="P002",
            descricao="Fundo de gaveta",
            quantidade_planejada=1,
            plano="04",
            roteiro="COR > MCX > CQL > EXP",
        )
        self.peca_lateral = PecaPCP.objects.create(
            modulo=self.modulo,
            referencia_bruta="M1001 - P003",
            codigo_modulo="M1001",
            codigo_peca="P003",
            descricao="Lateral de gaveta",
            quantidade_planejada=1,
            plano="04",
            roteiro="COR > BOR > USI > FUR > MCX > CQL > EXP",
        )

    def test_registra_separacao_destino_uma_unica_vez(self):
        resultado = registrar_separacao_destino({
            "pid": self.pid,
            "codigo_peca": "P001",
            "quantidade": 1,
            "usuario": "operador",
        })

        self.assertTrue(resultado["sucesso"])
        self.assertEqual(
            EventoOperacional.objects.filter(etapa=EtapaOperacional.SEPARACAO_DESTINOS).count(),
            1,
        )

        repetido = registrar_separacao_destino({
            "pid": self.pid,
            "codigo_peca": "P001",
            "quantidade": 1,
            "usuario": "operador",
        })
        self.assertTrue(repetido["sucesso"])
        self.assertTrue(repetido["repetido"])
        self.assertEqual(
            EventoOperacional.objects.filter(etapa=EtapaOperacional.SEPARACAO_DESTINOS).count(),
            1,
        )

    def test_fluxo_envio_registra_entrada_e_saida(self):
        criado = criar_envio_expedicao({
            "codigo": "ENV-TESTE",
            "descricao": "Carga parcial",
            "motorista": "Joao",
            "ajudante": "Carlos",
            "destino_principal": "Obra Centro",
            "destinos_secundarios": ["Predio A", "Predio B"],
            "usuario": "pcp",
        })
        self.assertTrue(criado["sucesso"])

        vinculo = adicionar_item_envio({
            "envio_codigo": "ENV-TESTE",
            "pid": self.pid,
            "codigo_peca": "P001",
            "quantidade": 1,
            "usuario": "pcp",
        })
        self.assertTrue(vinculo["sucesso"])

        entrada = registrar_entrada_expedicao({
            "envio_codigo": "ENV-TESTE",
            "usuario": "expedicao",
        })
        self.assertTrue(entrada["sucesso"])

        saida = registrar_saida_expedicao({
            "envio_codigo": "ENV-TESTE",
            "usuario": "expedicao",
        })
        self.assertTrue(saida["sucesso"])

        envio = EnvioExpedicao.objects.get(codigo="ENV-TESTE")
        self.assertEqual(envio.status, StatusEnvioExpedicao.LIBERADO)
        self.assertEqual(
            EventoOperacional.objects.filter(
                etapa=EtapaOperacional.EXPEDICAO,
                movimento=MovimentoOperacional.ENTRADA,
            ).count(),
            1,
        )
        self.assertEqual(
            EventoOperacional.objects.filter(
                etapa=EtapaOperacional.EXPEDICAO,
                movimento=MovimentoOperacional.SAIDA,
            ).count(),
            1,
        )
        self.assertEqual(envio.motorista, "Joao")
        self.assertEqual(envio.ajudante, "Carlos")
        self.assertEqual(envio.destino_principal, "Obra Centro")
        self.assertEqual(envio.destinos_secundarios, ["Predio A", "Predio B"])

    def test_modulo_fica_parcial_quando_pecas_chegam_em_tempos_diferentes_ao_mcx(self):
        registrar_evento_peca({
            "pid": self.pid,
            "codigo_peca": "P002",
            "etapa": EtapaOperacional.CORTE.value,
            "quantidade": 1,
            "usuario": "operador",
        })
        registrar_evento_peca({
            "pid": self.pid,
            "codigo_peca": "P003",
            "etapa": EtapaOperacional.CORTE.value,
            "quantidade": 1,
            "usuario": "operador",
        })
        registrar_evento_peca({
            "pid": self.pid,
            "codigo_peca": "P003",
            "etapa": EtapaOperacional.BORDA.value,
            "quantidade": 1,
            "usuario": "operador",
        })

        modulos = list_modulos_preenchimento(self.pid)
        modulo = next(item for item in modulos if item["codigo_modulo"] == "M1001")
        setor_mcx = next(item for item in modulo["setores"] if item["setor"] == EtapaOperacional.MCX.value)

        self.assertEqual(setor_mcx["status"], "parcial")
        self.assertEqual(setor_mcx["liberadas"], 1)
        self.assertEqual(setor_mcx["pendentes"], 1)
        self.assertEqual(setor_mcx["pecas_prontas"][0]["codigo_peca"], "P002")
        self.assertEqual(setor_mcx["pecas_pendentes"][0]["codigo_peca"], "P003")
        self.assertIn("Usinagem", setor_mcx["pecas_pendentes"][0]["pendencias"])

        auditoria = list_auditoria_pecas(self.pid)
        lateral = next(item for item in auditoria if item["codigo_peca"] == "P003")
        self.assertEqual(lateral["proxima_etapa"], EtapaOperacional.USINAGEM.value)
        self.assertFalse(lateral["aguardando_preenchimento_modulo"])

    def test_tela_operacional_renderiza_para_usuario_autenticado(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("bipagem:operacional_lote", args=[self.pid]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Preenchimento do Modulo por Setor")
        self.assertContains(response, "Auditoria de Pecas")

    def test_adiciona_modulo_inteiro_na_viagem(self):
        criar_envio_expedicao({
            "codigo": "ENV-MOD",
            "descricao": "Carga completa",
            "usuario": "pcp",
        })

        resultado = adicionar_modulo_envio({
            "envio_codigo": "ENV-MOD",
            "pid": self.pid,
            "codigo_modulo": "M1001",
            "usuario": "pcp",
        })

        self.assertTrue(resultado["sucesso"])
        envio = EnvioExpedicao.objects.get(codigo="ENV-MOD")
        self.assertEqual(envio.itens.count(), 3)
