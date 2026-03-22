from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    """ hierarquia """
NIVEL_CHOICES = (
    ('admin', 'Administrador'),
    ('supervisor', 'Supervidor do Setor'),
    ('operador', 'Operador, Assistente'),
)

nivel = models.CharField(
    max_length=20,
    choices=NIVEL_CHOICES,
    default='operador'
)

def __str__(self):
    return f"{self.username} ({self.get_nivel_display()})"
