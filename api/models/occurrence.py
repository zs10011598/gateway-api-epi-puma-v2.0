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
    p_30a39 = models.FloatField(db_column='P_30A39')
    p_18a29 = models.FloatField(db_column='P_18A29')

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
    sexo = models.CharField(max_length=50)
    neumonia = models.CharField(max_length=10)
    embarazo = models.CharField(max_length=10)
    diabetes = models.CharField(max_length=10)
    epoc = models.CharField(max_length=10)
    asma = models.CharField(max_length=10)
    inmusupr = models.CharField(max_length=10)
    hipertension = models.CharField(max_length=10)
    cardiovascular = models.CharField(max_length=10)
    obesidad = models.CharField(max_length=10)
    renal_cronica = models.CharField(max_length=10)
    tabaquismo = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'occurrence' 


class OccurrenceVaccines(models.Model):

    variable_id = models.IntegerField(db_column='covariable_id')
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    date_occurrence = models.DateField()
    edad = models.IntegerField(db_column='edad_a')

    class Meta:
        managed = False
        db_table = 'occurrence' 


class OccurrenceVaccinesSummarized(models.Model):

    variable_id = models.IntegerField(db_column='covariable_id')
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    date_occurrence = models.DateField()
    edad = models.IntegerField(db_column='edad_a')
    occ = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'occurrence_summary' 


class OccurrenceIRAG(models.Model):

    var = models.CharField(max_length=255)
    value = models.FloatField()
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    date_occurrence = models.DateField()

    class Meta:
        managed = False
        db_table = 'occurrence'