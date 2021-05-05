from django.db import models



class Variable(models.Model):

    class Meta:
        managed = False
        db_table = 'covariable' 


class VariableCOVID19(models.Model):
    resultado_lab = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'covariable' 