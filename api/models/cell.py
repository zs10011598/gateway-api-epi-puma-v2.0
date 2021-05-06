from django.db import models
from django.contrib.auth.models import User as DjangoUser



class CellState(models.Model):
    gridid_state = models.CharField(max_length=2)
    name = models.CharField(max_length=50)
    pobtot = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'mesh_state' 


class CellMunicipality(models.Model):
    gridid_mun = models.CharField(max_length=5)
    state = models.ForeignKey(CellState, models.DO_NOTHING, blank=True, null=True)
    gridid_state = models.CharField(max_length=2)
    state_name = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    pobtot = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'mesh_mun'   


class CellAGEB(models.Model):
    gridid_ageb = models.CharField(max_length=10)
    gridid_mun = models.CharField(max_length=2)
    gridid_state = models.CharField(max_length=5)
    state_name = models.CharField(max_length=50)
    municipality_name = models.CharField(max_length=200)
    state = models.ForeignKey(CellState, models.DO_NOTHING, blank=True, null=True)
    mun = models.ForeignKey(CellMunicipality, models.DO_NOTHING, blank=True, null=True)
    pobtot = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'mesh_ageb'


class GeomState(models.Model):
    pass