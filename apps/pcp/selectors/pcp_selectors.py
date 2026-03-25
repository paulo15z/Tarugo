from apps.pcp.models.processamento import ProcessamentoPCP


def get_historico_pcp():
    return ProcessamentoPCP.objects.all().order_by('-data')