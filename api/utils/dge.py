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
import numpy as np
import random
import string



def calculate_results_covariables(target, occurrences):
    """
        Description: calculate epsilon, score, etc for covariables
        'HOSPITALIZADO', 'NEUMONIA', 'INTUBADO', 'FALLECIDO'
    """
    results_covariables = []
    target_column_map = {'HOSPITALIZADO': 'hospitalizado', 'NEUMONIA': 'neumonia', 'INTUBADO': 'intubado', 'UCI': 'uci'}
    
    df_train = pd.DataFrame(occurrences)
    occurrences = None
    df_train = df_train.rename(columns={'tipo_paciente': 'hospitalizado'})
    df_train = df_train.drop(columns=['gridid_state', 'gridid_ageb', 'date_occurrence'])
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


    if target == 'UCI':
        variables.append('hospitalizado')
    elif target == 'NEUMONIA':
        variables.append('uci')
        variables.append('hospitalizado')
    elif target == 'INTUBADO':
        variables.append('uci')
        variables.append('hospitalizado')
        variables.append('neumonia')
    elif target == 'FALLECIDO':
        variables.append('uci')
        variables.append('hospitalizado')
        variables.append('neumonia')
        variables.append('intubado')
    
    dict_values = {}
    for variable in variables:
        variable_row = df_train[variable].unique().tolist()
        dict_values[variable] = variable_row

    #print(dict_values)
    
    N = df_train.shape[0]
    target_column = None

    #print(df_train['fecha_def'].unique())
    if target == 'FALLECIDO':
        Nc = df_train[df_train['fecha_def']!='9999-99-99'].shape[0]
    elif target == 'HOSPITALIZADO':
        target_column = target_column_map[target]
        Nc = df_train[df_train[target_column]=='HOSPITALIZADO'].shape[0]
    else:
        target_column = target_column_map[target]
        Nc = df_train[df_train[target_column]=='SI'].shape[0]

    #print('Nc = ', Nc)
    
    #alpha = 0.00000005
    alpha = 0.0005

    for variable in variables:

        values = dict_values[variable]
        
        #print(variable, values)
        
        for value in values:
            filter_variable = variable
            filter_value = value
            
            if target == 'FALLECIDO':
                Ncx = df_train[(df_train[filter_variable]==filter_value) & (df_train['fecha_def']!='9999-99-99')].shape[0]
            elif target == 'HOSPITALIZADO':
                Ncx = df_train[(df_train[filter_variable]==filter_value) & (df_train[target_column]=='HOSPITALIZADO')].shape[0]
            else:
                Ncx = df_train[(df_train[filter_variable]==filter_value) & (df_train[target_column]=='SI')].shape[0]
            
            Nx = df_train[df_train[variable]==value].shape[0]
            
            Nc_x = Nx - Ncx
            PCX = Ncx/Nx
            Nc_ = N - Nc
            P_CX = Nc_x/Nx
            P_C = Nc_/N
            PC = Nc/N
            try:
                s0 = np.log(PC/P_C)
                epsilon = (Nx*(PCX - PC)) / ((Nx*PC*(1 - PC))**0.5)
                #score = np.log((Ncx/Nc + alpha)/(Nc_x/Nc_ + 2*alpha))
                score = np.log(((Ncx + alpha)/(Nc + 2*alpha))/((Nc_x + alpha)/(Nc_+ 2*alpha)))
            except Exception as e:
                #print(str(e))
                s0 = 0
                epsilon = 0
                score = 0
            
            if np.sign(epsilon) != np.sign(score):
                if variable != 'gridid_mun':
                    print('IIIIIIIII->', N, Nc, Ncx, Nx, epsilon, score, variable, value)
                else:
                    print(N, Nc, Ncx, Nx, epsilon, score, variable, value)

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

    if target == 'UCI':
        variables.append('hospitalizado')
    elif target == 'NEUMONIA':
        variables.append('hospitalizado')
        variables.append('uci')
    elif target == 'INTUBADO':
        variables.append('hospitalizado')
        variables.append('uci')
        variables.append('neumonia')
    elif target == 'FALLECIDO':
        variables.append('hospitalizado')
        variables.append('uci')
        variables.append('neumonia')
        variables.append('intubado')

    results_covariables = calculate_results_covariables(target, occurrences)
    df_covars = pd.DataFrame(results_covariables)
    #print(df_covars.columns)
    s0 = df_covars.iloc[0]['s0']
    results_covariables = None
    
    for occ in occurrences:
        
        score = s0
        score_hospitalizado = s0
        score_uci = s0
        score_neumonia = s0
        score_hospitalizado_uci = s0
        score_hospitalizado_neumonia = s0
        score_uci_neumonia = s0 
        score_hospitalizado_uci_neumonia = s0
        score_hospitalizado_intubado = s0
        score_uci_intubado = s0
        score_neumonia_intubado = s0
        score_intubado = s0 
        score_hospitalizado_neumonia_intubado = s0
        score_hospitalizado_uci_intubado = s0
        score_uci_neumonia_intubado = s0
        score_hospitalizado_uci_neumonia_intubado = s0

        occ['edad'] = map_age_group(occ['edad'])
        
        for variable in variables:
            
            #print('VARIABLE', variable, occ)
            current_score = df_covars[(df_covars['variable'] == variable) &\
                (df_covars['value'] == occ[variable if variable != 'hospitalizado' else 'tipo_paciente'])] \
                ['score'].iloc[0]

            score += current_score
            if target == 'UCI':
                if variable != 'hospitalizado':
                    score_hospitalizado += current_score
            if target == 'NEUMONIA':
                if variable != 'hospitalizado':
                    score_hospitalizado += current_score
                if variable != 'uci':
                    score_uci += current_score
                if variable != 'hospitalizado' and variable != 'uci':
                    score_hospitalizado_uci += current_score
            if target == 'INTUBADO':
                if variable != 'hospitalizado':
                    score_hospitalizado += current_score
                if variable != 'uci':
                    score_uci += current_score
                if variable != 'neumonia':
                    score_neumonia += current_score
                if variable != 'hospitalizado' and variable != 'uci':
                    score_hospitalizado_uci += current_score
                if variable != 'hospitalizado' and variable != 'neumonia':
                    score_hospitalizado_neumonia += current_score
                if variable != 'uci' and variable != 'neumonia':
                    score_uci_neumonia += current_score
                if variable != 'hospitalizado' and variable != 'uci' and variable != 'neumonia':
                    score_hospitalizado_uci_neumonia += current_score
            if target == 'FALLECIDO':
                if variable != 'hospitalizado':
                    score_hospitalizado += current_score
                if variable != 'uci':
                    score_uci += current_score
                if variable != 'neumonia':
                    score_neumonia += current_score
                if variable != 'intubado':
                    score_intubado += current_score
                if variable != 'hospitalizado' and variable != 'uci':
                    score_hospitalizado_uci += current_score
                if variable != 'hospitalizado' and variable != 'neumonia':
                    score_hospitalizado_neumonia += current_score
                if variable != 'hospitalizado' and variable != 'intubado':
                    score_hospitalizado_intubado += current_score
                if variable != 'uci' and variable != 'neumonia':
                    score_uci_neumonia += current_score
                if variable != 'uci' and variable != 'intubado':
                    score_uci_intubado += current_score
                if variable != 'neumonia' and variable != 'intubado':
                    score_neumonia_intubado += current_score
                if variable != 'hospitalizado' and variable != 'uci' and variable != 'neumonia':
                    score_hospitalizado_uci_neumonia += current_score
                if variable != 'hospitalizado' and variable != 'uci' and variable != 'intubado':
                    score_hospitalizado_uci_intubado += current_score
                if variable != 'hospitalizado' and variable != 'neumonia' and variable != 'intubado':
                    score_hospitalizado_neumonia_intubado += current_score
                if variable != 'uci' and variable != 'neumonia' and variable != 'intubado':
                    score_uci_neumonia_intubado += current_score
                if variable != 'hospitalizado' and variable != 'uci' and variable != 'neumonia' and variable != 'intubado':
                    score_hospitalizado_uci_neumonia_intubado += current_score
        
        occ['score'] = score

        occ['score_h'] = score_hospitalizado
        
        occ['score_hu'] = score_hospitalizado_uci
        occ['score_u'] = score_uci

        occ['score_n'] = score_neumonia
        occ['score_hn'] = score_hospitalizado_neumonia
        occ['score_un'] = score_uci_neumonia
        occ['score_hun'] = score_hospitalizado_uci_neumonia

        occ['score_i'] = score_intubado
        occ['score_hi'] = score_hospitalizado_intubado
        occ['score_ui'] = score_uci_intubado
        occ['score_ni'] = score_neumonia_intubado
        occ['score_hui'] = score_hospitalizado_uci_intubado
        occ['score_hni'] = score_hospitalizado_neumonia_intubado
        occ['score_uni'] = score_uci_neumonia_intubado
        occ['score_huni'] = score_hospitalizado_uci_neumonia_intubado

    return occurrences


def is_target(x, target):
    """
        Description: Decides if a record is target
    """
    target_column_map = {
        'HOSPITALIZADO': 'tipo_paciente', 
        'NEUMONIA': 'neumonia', 
        'INTUBADO': 'intubado',
        'UCI': 'uci'}

    if target == 'CONFIRMADO':
        if x['variable_id'] in [5, 2, 3, 7]:
            return 1
        else:
            return 0 
    elif target == 'FALLECIDO':
        if x['variable_id'] in [5, 2, 3, 7] and x['fecha_def'] != '9999-99-99':
            return 1
        else:
            return 0
    elif target == 'HOSPITALIZADO':
        if x['variable_id'] in [5, 2, 3, 7] and x[target_column_map[target]]=='HOSPITALIZADO':
            return 1
        else:
            return 0
    else:
        if x['variable_id'] in [5, 2, 3, 7] and x[target_column_map[target]]=='SI':
            return 1
        else:
            return 0


def is_target_query(d, target):
    """
        Description: Decides if a record is target
    """
    target_column_map = {
        'HOSPITALIZADO': 'tipo_paciente', 
        'NEUMONIA': 'neumonia', 
        'INTUBADO': 'intubado',
        'UCI': 'uci'}

    if target == 'FALLECIDO':
        pass
    elif target == 'HOSPITALIZADO':
        d[target_column_map[target]]='HOSPITALIZADO'
    else:
        d[target_column_map[target]]='SI'


def calculate_results_cells_free_mode(df_covars, variables, target, occurrences):
    """
        Description: calculate score and probability for cells
    """

    s0 = df_covars.iloc[0]['s0']
    results_covariables = None
    
    for occ in occurrences:

        #print(occ, is_target(occ, target))
        #if is_target(occ, target) == 0:
        #    occ['target'] = int(0)
        #    continue
        #else:
        #    occ['target'] = int(1)
        
        score = s0
        occ['edad'] = map_age_group(occ['edad'])
        
        for variable in variables:
            
            #print('VARIABLE', variable, occ[variable if variable != 'hospitalizado' else 'tipo_paciente'])
            try:
                current_score = df_covars[(df_covars['variable'] == variable) &\
                    (df_covars['value'] == occ[variable if variable != 'hospitalizado' else 'tipo_paciente'])] \
                    ['score'].iloc[0]

                score += current_score
            except:
                print('VARIABLE', variable, occ[variable if variable != 'hospitalizado' else 'tipo_paciente'], ' hasnt score')
            
        
        occ['score'] = score

    return occurrences


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str