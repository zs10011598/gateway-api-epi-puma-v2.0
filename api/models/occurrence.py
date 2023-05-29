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
    uci = models.CharField(max_length=15)
    intubado = models.CharField(max_length=15)
    tipo_paciente = models.CharField(max_length=20)

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


class OccurrenceEpiSpecies(models.Model):

    reino = models.CharField(max_length=255)
    phylum = models.CharField(max_length=255)
    clase = models.CharField(max_length=255)
    orden = models.CharField(max_length=255)
    familia = models.CharField(max_length=255)
    genero = models.CharField(max_length=255)
    nombrecientifico = models.CharField(max_length=255)
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    gridid_64km = models.CharField(max_length=10)
    gridid_32km = models.CharField(max_length=10)
    gridid_16km = models.CharField(max_length=10)
    nombreenfermedad= models.CharField(max_length=10)
    sexo = models.CharField(max_length=2)
    edad = models.IntegerField()
    numeroindividuos = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'ocurrence'


class OccurrenceSNIB(models.Model):

    reinovalido = models.CharField(max_length=255)
    phylumdivisionvalido = models.CharField(max_length=255)
    clasevalida = models.CharField(max_length=255)
    ordenvalido = models.CharField(max_length=255)
    familiavalida = models.CharField(max_length=255)
    generovalido = models.CharField(max_length=255)
    especievalida = models.CharField(max_length=255)
    gridid_state = models.CharField(max_length=2) 
    gridid_mun = models.CharField(max_length=5)
    gridid_ageb = models.CharField(max_length=10)
    gridid_64km = models.CharField(max_length=10)
    gridid_32km = models.CharField(max_length=10)
    gridid_16km = models.CharField(max_length=10)

    class Meta:
        managed = False
        db_table = 'ocurrence'



class OccurrenceFutureWorldclim(models.Model):

    variable_id = models.IntegerField(db_column='covariable_id')
    gridid_mun = models.CharField(max_length=5)
    date_occurrence = models.DateField()
    ssp = models.CharField(max_length=10)
    period = models.CharField(max_length=50)
    gcm = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'occurrence'