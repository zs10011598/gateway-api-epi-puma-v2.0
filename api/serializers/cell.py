from rest_framework import serializers


class CellStateSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    gridid_state = serializers.CharField(max_length=2)
    name = serializers.CharField(max_length=50)
    pobtot = serializers.IntegerField()


class CellMunicipalitySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    state = CellStateSerializer()
    gridid_state = serializers.CharField(max_length=2)
    gridid_mun = serializers.CharField(max_length=5)
    state_name = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=200)
    pobtot = serializers.IntegerField()


class CellAGEBSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    state = CellStateSerializer()
    mun = CellMunicipalitySerializer()
    gridid_state = serializers.CharField(max_length=2)
    gridid_mun = serializers.CharField(max_length=5)
    gridid_ageb = serializers.CharField(max_length=10)
    state_name = serializers.CharField(max_length=50)
    municipality_name = serializers.CharField(max_length=200)
    pobtot = serializers.IntegerField()