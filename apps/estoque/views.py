from rest_framework import viewsets
from .models import MaterialType, Location, MDFSheet, CutOff
from .serializers import MaterialTypeSerializer, LocationSerializer, MDFSheetSerializer, CutOffSerializer

class MaterialTypeViewSet(viewsets.ModelViewSet):
    queryset = MaterialType.objects.all()
    serializer_class = MaterialTypeSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class MDFSheetViewSet(viewsets.ModelViewSet):
    queryset = MDFSheet.objects.all()
    serializer_class = MDFSheetSerializer

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

class CutOffViewSet(viewsets.ModelViewSet):
    queryset = CutOff.objects.all()
    serializer_class = CutOffSerializer

    @action(detail=False, methods=['post'], url_path='generate-from-sheet')
    def generate_from_sheet(self, request):
        """
        Gera uma sobra de corte a partir de uma chapa de MDF.
        Reduz a quantidade da chapa original (ou a remove se for a última)
        e cria um novo registro de retalho.
        """
        sheet_id = request.data.get('sheet_id')
        width = request.data.get('width')
        height = request.data.get('height')
        quantity = request.data.get('quantity', 1)

        try:
            sheet = MDFSheet.objects.get(id=sheet_id)
        except MDFSheet.DoesNotExist:
            return Response({"error": "Chapa não encontrada"}, status=status.HTTP_404_NOT_FOUND)

        if sheet.quantity < int(quantity):
            return Response({"error": "Quantidade insuficiente na chapa original"}, status=status.HTTP_400_BAD_REQUEST)

        # Criar o retalho
        cutoff = CutOff.objects.create(
            material_type=sheet.material_type,
            width=width,
            height=height,
            thickness=sheet.thickness,
            quantity=quantity,
            location=sheet.location,
            origin_sheet=sheet,
            notes=f"Gerado a partir da chapa {sheet.id}"
        )

        # Atualizar a chapa original
        sheet.quantity -= int(quantity)
        if sheet.quantity == 0:
            sheet.delete()
        else:
            sheet.save()

        return Response(CutOffSerializer(cutoff).data, status=status.HTTP_201_CREATED)

