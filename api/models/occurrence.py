from django.db import models
from .variable import *


class Occurrence(models.Model):

    variable_id = models.IntegerField(db_column='covariable_id')
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    date_occurrence = models.DateField()

    class Meta:
        managed = False
        db_table = 'occurrence' 