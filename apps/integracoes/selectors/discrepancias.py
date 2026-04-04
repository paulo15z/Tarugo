# apps/integracoes/selectors/discrepancias.py
from django.db.models import Q, Count
from apps.bipagem.models.evento_bipagem import EventoBipagem
from apps.bipagem.models.peca import Peca
from apps.integracoes.models import MapeamentoMaterial

class DiscrepanciaSelector:
    """
    Selector especializado em identificar falhas entre o Digital e o Físico.
    Segue o padrão tarugo-architecture: centraliza queries complexas.
    """

    @staticmethod
    def get_eventos_com_erro():
        """Retorna eventos de bipagem que falharam na sincronização com o estoque."""
        return EventoBipagem.objects.filter(
            erro_sincronia__isnull=False
        ).select_related('peca__modulo__ordem_producao__pedido').order_by('-momento')

    @staticmethod
    def get_pecas_sem_mapeamento():
        """
        Identifica peças bipadas cujo material não possui um mapeamento de estoque.
        Isso é uma discrepância crítica para o Gêmeo Digital.
        """
        # Materiais mapeados
        materiais_mapeados = MapeamentoMaterial.objects.filter(
            ativo=True
        ).values_list('nome_dinabox', flat=True)

        return Peca.objects.filter(
            status='BIPADA'
        ).exclude(
            material__in=materiais_mapeados
        ).select_related('modulo__ordem_producao__pedido').order_by('-data_bipagem')

    @staticmethod
    def get_resumo_estatistico():
        """Retorna números rápidos para o dashboard."""
        return {
            'total_erros_sincronia': EventoBipagem.objects.filter(erro_sincronia__isnull=False).count(),
            'total_sem_mapeamento': Peca.objects.filter(status='BIPADA').exclude(
                material__in=MapeamentoMaterial.objects.filter(ativo=True).values_list('nome_dinabox', flat=True)
            ).count(),
            'total_mapeamentos_ativos': MapeamentoMaterial.objects.filter(ativo=True).count()
        }
