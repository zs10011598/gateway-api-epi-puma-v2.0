from rest_framework import serializers



class VariableINEGI2020Serializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    interval = serializers.CharField(max_length=100)
    bin = serializers.IntegerField()
    code = serializers.CharField(max_length=100)
    lim_inf = serializers.FloatField()
    lim_sup = serializers.FloatField()
    mesh = serializers.CharField(max_length=5)