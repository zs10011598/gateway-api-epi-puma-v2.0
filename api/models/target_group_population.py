from django.db import models
from django.contrib.auth.models import User as DjangoUser

from .cell import CellMunicipality, CellState, CellAGEB


class TargetGroupCatalogue(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'target_group_catalogue' 


class TargetGroupPopulation(models.Model):
    target_group = models.ForeignKey(TargetGroupCatalogue, models.DO_NOTHING, blank=True, null=True)
    mun_id = models.ForeignKey(CellMunicipality, models.DO_NOTHING, blank=True, null=True)
    state_id = models.ForeignKey(CellState, models.DO_NOTHING, blank=True, null=True)
    ageb_id = models.ForeignKey(CellAGEB, models.DO_NOTHING, blank=True, null=True)
    population = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'target_group_population'