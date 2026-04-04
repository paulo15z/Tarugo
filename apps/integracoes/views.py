# apps/integracoes/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.integracoes.selectors.discrepancias import DiscrepanciaSelector

@login_required
def dashboard_discrepancias(request):
    """
    Dashboard do Gêmeo Digital: Exibe falhas de sincronia entre Digital e Físico.
    Segue o padrão tarugo-architecture: View chama Selector.
    """
    
    # Camada de Dados (Selector)
    eventos_erro = DiscrepanciaSelector.get_eventos_com_erro()
    pecas_sem_map = DiscrepanciaSelector.get_pecas_sem_mapeamento()
    estatisticas = DiscrepanciaSelector.get_resumo_estatistico()

    # Camada de Apresentação (Template)
    context = {
        'eventos_erro': eventos_erro,
        'pecas_sem_map': pecas_sem_map,
        'estatisticas': estatisticas,
        'total_discrepancias': estatisticas['total_erros_sincronia'] + estatisticas['total_sem_mapeamento']
    }
    
    return render(request, 'integracoes/dashboard_discrepancias.html', context)
