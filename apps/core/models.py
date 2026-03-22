from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Adicione campos personalizados aqui, se necessário
    # Por exemplo: phone_number = models.CharField(max_length=15, blank=True, null=True)
    pass

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return self.username
