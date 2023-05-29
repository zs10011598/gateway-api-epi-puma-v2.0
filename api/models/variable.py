from django.db import models
from django.contrib.postgres.fields import ArrayField



class Variable(models.Model):

    cells_state = ArrayField(models.CharField(max_length=10, blank=True))
    cells_mun = ArrayField(models.CharField(max_length=10, blank=True))
    cells_ageb = ArrayField(models.CharField(max_length=10, blank=True))

    class Meta:
        managed = False
        db_table = 'covariable' 


class VariableCOVID19(models.Model):
    resultado_lab = models.CharField(max_length=100)
    cells_state = ArrayField(models.CharField(max_length=10, blank=True))
    cells_mun = ArrayField(models.CharField(max_length=10, blank=True))
    cells_ageb = ArrayField(models.CharField(max_length=10, blank=True))    

    class Meta:
        managed = False
        db_table = 'covariable' 


class VariableINEGI2020(models.Model):
    name = models.CharField(max_length=100)
    interval = models.CharField(max_length=100)
    bin = models.IntegerField()
    code = models.CharField(max_length=100)
    lim_inf = models.FloatField()
    lim_sup = models.FloatField()
    mesh = models.CharField(max_length=5)
    cells_state = ArrayField(models.CharField(max_length=10, blank=True))
    cells_mun = ArrayField(models.CharField(max_length=10, blank=True))
    cells_ageb = ArrayField(models.CharField(max_length=10, blank=True))    

    class Meta:
        managed = False
        db_table = 'covariable' 


class VariableIRAG(models.Model):
    name = models.CharField(max_length=100)
    bin = models.IntegerField()
    description = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'covariable' 


class VariableHistorical(models.Model):
    name = models.CharField(max_length=100)
    bin = models.IntegerField()
    description = models.CharField(max_length=100)
    tag = models.CharField(max_length=100)


class VariableSNIB(models.Model):
    reinovalido = models.CharField(max_length=255)
    phylumdivisionvalido = models.CharField(max_length=255)
    clasevalida = models.CharField(max_length=255)
    ordenvalido = models.CharField(max_length=255)
    familiavalida = models.CharField(max_length=255)
    generovalido = models.CharField(max_length=255)
    especievalida = models.CharField(max_length=255)
    cells_state = ArrayField(models.CharField(max_length=10, blank=True))
    cells_mun = ArrayField(models.CharField(max_length=10, blank=True))
    cells_ageb = ArrayField(models.CharField(max_length=10, blank=True))

    class Meta:
        managed = False
        db_table = 'covariable' 


class VariableWorldclim(models.Model):

    label = models.CharField(max_length=255)
    interval = models.CharField(max_length=255)
    layer = models.CharField(max_length=255)
    icat = models.IntegerField()
    cells_state = ArrayField(models.CharField(max_length=10, blank=True))
    cells_mun = ArrayField(models.CharField(max_length=10, blank=True))
    cells_ageb = ArrayField(models.CharField(max_length=10, blank=True))

    class Meta:
        managed = False
        db_table = 'covariable' 


class VariableFutureWorldclim(models.Model):

    label = models.CharField(max_length=255)
    interval = models.CharField(max_length=255)
    layer = models.CharField(max_length=255)
    icat = models.IntegerField()
    cells_state = ArrayField(models.CharField(max_length=10, blank=True))
    cells_mun = ArrayField(models.CharField(max_length=10, blank=True))
    cells_ageb = ArrayField(models.CharField(max_length=10, blank=True))
    ssp = models.CharField(max_length=10)
    period = models.CharField(max_length=50)
    gcm = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'covariable' 