from rest_framework import serializers
from .models import MaterialType, Location, MDFSheet, CutOff

class MaterialTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialType
        fields = '__all__'

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class MDFSheetSerializer(serializers.ModelSerializer):
    material_type_name = serializers.CharField(source='material_type.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = MDFSheet
        fields = '__all__'

class CutOffSerializer(serializers.ModelSerializer):
    material_type_name = serializers.CharField(source='material_type.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    origin_sheet_info = serializers.CharField(source='origin_sheet.__str__', read_only=True)

    class Meta:
        model = CutOff
        fields = '__all__'
