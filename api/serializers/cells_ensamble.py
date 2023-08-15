from rest_framework import serializers


class SpeciesCellsEnsamble(serializers.Serializer):
    taxon = serializers.CharField(max_length=50)
    value = serializers.CharField(max_length=50)


class TargetCellsEnsamble(serializers.Serializer):
    species = SpeciesCellsEnsamble()
    disease = serializers.CharField(max_length=50, required=False)
    agent = serializers.CharField(max_length=50, required=False)


class CovariableFilterCellsEnsamble(serializers.Serializer):
    snib = serializers.ListField(child=SpeciesCellsEnsamble(), required=False)
    inegi2020 = serializers.ListField(child=SpeciesCellsEnsamble(), required=False)
    worldclim = serializers.ListField(child=SpeciesCellsEnsamble(), required=False)


class TargetAttributeCellsEnsamble(serializers.Serializer):
    attribute = serializers.CharField(max_length=50)
    value = serializers.CharField(max_length=50)
    operator = serializers.CharField(max_length=10)


class EnsambleCellsRequest(serializers.Serializer):
    target = TargetCellsEnsamble()
    mesh = serializers.CharField(max_length=50)
    covariables = serializers.ListField(child=serializers.CharField())
    covariable_filter = CovariableFilterCellsEnsamble()
    target_attribute_filter = serializers.ListField(child=TargetAttributeCellsEnsamble())
    lim_inf_first = serializers.DateField(required=False)
    lim_sup_first = serializers.DateField(required=False)
    lim_inf_training = serializers.DateField(required=False)
    lim_sup_training = serializers.DateField(required=False)
    lim_inf_validation = serializers.DateField(required=False)
    lim_sup_validation = serializers.DateField(required=False)
    selected_decile = serializers.ListField(child=serializers.IntegerField(), required=False)
    validation = serializers.BooleanField(required=True)