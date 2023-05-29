from django.db import models
from django.contrib.postgres.fields import ArrayField


class WorldclimResults(models.Model):
    score = models.FloatField()
    cells_mun = ArrayField(models.CharField(max_length=10, blank=True))
    tag = models.CharField(max_length=30)
    bid = models.IntegerField()
    icat = models.IntegerField()
    layer = models.CharField(max_length=50)
    id_analysis = models.IntegerField()
    
    class Meta:
        managed = False
        db_table = 'worldclim_analysis_score' 