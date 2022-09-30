import json
from ..models.cell import *
from django.db.models import Sum, Count
from ..models.variable import *
from ..serializers.variable import *
from .helpers import *
from ..models.occurrence import *
import numpy as np
import pandas as pd
from ..serializers.cell import *
from sklearn.linear_model import LinearRegression
import datetime as dt


def calculate_results_covariables(target, occurrences):
    """
        Description: calculate epsilon, score, etc for covariables
        'CONFIRMADO', 'HOSPITALIZADO', 'NEUMONIA', 'INTUBADO', 'FALLECIDO'
    """
    results_covariables = []
    target_column_map = {'HOSPITALIZADO': 'uci', 'NEUMONIA': 'neumonia', 'INTUBADO': 'intubado'}
    
    df_train = pd.DataFrame(occurrences)
    occurrences = None
    df_train = df_train.drop(columns=['gridid_state', 'gridid_ageb', 'date_occurrence', 'fecha_def'])
    df_train['edad'] = df_train['edad'].apply(lambda x: map_age_group(x))
    dict_results = {
        'variable': [], 
        'valor': [], 
        'Nx': [], 
        'Ncx': [], 
        'PCX': [], 
        'PC': [], 
        'Nc': [], 
        'N': [], 
        'epsilon': [],
        'Nc_': [],
        'Nc_x':[],
        'P_C': [],
        'P_CX':[],
        's0':[],
        'score':[]
    }
    variables = [
        'gridid_mun', 'edad', 
        'sexo', 'embarazo', 
        'diabetes', 'epoc', 
        'asma', 'inmusupr', 
        'hipertension', 'cardiovascular', 
        'obesidad', 'renal_cronica', 
        'tabaquismo']
    
    dict_values = {}
    for variable in variables:
        variable_row = df_train[variable].unique().tolist()
        dict_values[variable] = variable_row
    
    N = df_train.shape[0]
    target_column = None
    if target == 'CONFIRMADO' or target == 'FALLECIDO':
        Nc = df_train[df_train['variable_id'].isin([5, 2, 3, 7])].shape[0]
    else:
        target_column = target_column_map[target]
        Nc = df_train[(df_train['variable_id'].isin([5, 2, 3, 7])) & (df_train[target_column]=='SI')]\
            .shape[0]
    alpha = 0.01

    for variable in variables:
        values = dict_values[variable]
        
        for value in values:
            if target == 'CONFIRMADO' or target == 'FALLECIDO':
                Ncx = df_train[(df_train[variable]==value) & (df_train['variable_id'].isin([5, 2, 3, 7]))]\
                    [variable].count()
            else:
                Ncx = df_train[(df_train[variable]==value) & (df_train['variable_id'].isin([5, 2, 3, 7])) \
                    & (df_train[target_column]=='SI')][variable].count()
            Nx = df_train[df_train[variable]==value][variable].count()
            Nc_x = Nx - Ncx
            PCX = Ncx/Nx
            Nc_ = N - Nc
            P_CX = Nc_x/Nx
            P_C = Nc_/N
            PC = Nc/N
            try:
                s0 = np.log(PC/P_C)
                epsilon = (Nx*(PCX - PC))/ ((Nx*PC*(1 - PC))**0.5)
                score = np.log((Ncx/Nc + alpha)/(Nc_x/Nc_ + 2*alpha))
            except Exception as e:
                print(str(e))
                s0 = 0
                epsilon = 0
                score = 0
            results_covariables.append({
                'variable': variable,
                'value': value,
                'Nx': Nx, 
                'Ncx': Ncx, 
                'PCX': PCX, 
                'PC': PC, 
                'Nc': Nc, 
                'N': N, 
                'epsilon': epsilon,
                'Nc_': Nc_,
                'Nc_x': Nc_x,
                'P_C': P_C,
                'P_CX': P_CX,
                's0': s0,
                'score': score
            })
    
    df_train = None
    return results_covariables


def map_age_group(edad):
    """
        Description: get age group
    """
    if edad <= 17:
        return 'p_0a17'
    elif edad <= 29:
        return 'p_18a29'
    elif edad <= 39:
        return 'p_29a39'
    elif edad <= 49:
        return 'p_39a49'
    elif edad <= 59:
        return 'p_49a59'
    else:
        return 'p_60ymas'


def calculate_results_cells(target, occurrences):
    """
        Description: calculate score and probability for cells
    """
    variables = [
        'gridid_mun', 'edad', 
        'sexo', 'embarazo', 
        'diabetes', 'epoc', 
        'asma', 'inmusupr', 
        'hipertension', 'cardiovascular', 
        'obesidad', 'renal_cronica', 
        'tabaquismo']

    results_covariables = calculate_results_covariables(target, occurrences)
    df_covars = pd.DataFrame(results_covariables)
    s0 = df_covars.iloc[0]['s0']
    results_covariables = None
    for occ in occurrences:
        score = 0
        occ['edad'] = map_age_group(occ['edad'])
        occ['score'] = s0
        for variable in variables:
            score += df_covars[(df_covars['variable'] == variable) & (df_covars['value'] == occ[variable])]['score'].iloc[0]
        occ['score'] = score
    return occurrences
