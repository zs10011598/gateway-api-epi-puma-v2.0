from rest_framework import serializers



class TargetGroupCatalogueSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)