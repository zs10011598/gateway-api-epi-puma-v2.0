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


class OccurrenceINEGI2020(models.Model):

    variable_id = models.IntegerField(db_column='covariable_id')
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    date_occurrence = models.DateField()
    pobtot = models.IntegerField(db_column='POBTOT')
    p_60ymas = models.FloatField(db_column='P_60YMAS')
    p_50a59 = models.FloatField(db_column='P_50A59')
    p_40a49 = models.FloatField(db_column='P_40A49')

    class Meta:
        managed = False
        db_table = 'occurrence' 


class OccurrenceCOVID19(models.Model):

    variable_id = models.IntegerField(db_column='covariable_id')
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    date_occurrence = models.DateField()
    fecha_def = models.CharField(max_length=100)
    edad = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'occurrence' 


class OccurrenceVaccines(models.Model):

    variable_id = models.IntegerField(db_column='covariable_id')
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    date_occurrence = models.DateField()
    edad = models.IntegerField(db_column='EDAD')

    class Meta:
        managed = False
        db_table = 'occurrence' 