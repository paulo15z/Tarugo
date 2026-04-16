from django.db import models


class ProjetoStatus(models.TextChoices):
    AGUARDANDO_DEFINICOES = "AGUARDANDO_DEFINICOES", "Aguardando Definicoes"
    AGUARDANDO_PROJETISTA = "AGUARDANDO_PROJETISTA", "Aguardando Projetista"
    EM_DESENVOLVIMENTO = "EM_DESENVOLVIMENTO", "Em Desenvolvimento"
    EM_CONFERENCIA = "EM_CONFERENCIA", "Em Conferencia"
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO", "Aguardando Aprovacao"
    LIBERADO_PARA_PCP = "LIBERADO_PARA_PCP", "Liberado para PCP"
    CANCELADO = "CANCELADO", "Cancelado"
