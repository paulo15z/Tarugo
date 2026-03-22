from django.db import models
from django.conf import settings

class MaterialType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Tipo de Material")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Tipo de Material"
        verbose_name_plural = "Tipos de Materiais"

    def __str__(self):
        return self.name

class Location(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Localização")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")

    class Meta:
        verbose_name = "Localização"
        verbose_name_plural = "Localizações"

    def __str__(self):
        return self.name

class MDFSheet(models.Model):
    material_type = models.ForeignKey(MaterialType, on_delete=models.PROTECT, verbose_name="Tipo de Material")
    width = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Largura (mm)")
    height = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Altura (mm)")
    thickness = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Espessura (mm)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Localização")
    entry_date = models.DateTimeField(auto_now_add=True, verbose_name="Data de Entrada")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Chapa de MDF"
        verbose_name_plural = "Chapas de MDF"

    def __str__(self):
        return f"{self.material_type.name} - {self.width}x{self.height}mm ({self.quantity})"

class CutOff(models.Model):
    material_type = models.ForeignKey(MaterialType, on_delete=models.PROTECT, verbose_name="Tipo de Material")
    width = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Largura (mm)")
    height = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Altura (mm)")
    thickness = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Espessura (mm)")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantidade")
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Localização")
    origin_sheet = models.ForeignKey(MDFSheet, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Chapa de Origem", help_text="Chapa de MDF da qual esta sobra foi gerada")
    entry_date = models.DateTimeField(auto_now_add=True, verbose_name="Data de Entrada")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Sobra de Corte (Retalho)"
        verbose_name_plural = "Sobras de Corte (Retalhos)"

    def __str__(self):
        return f"Retalho {self.material_type.name} - {self.width}x{self.height}mm ({self.quantity})"
