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

### Por el momento los grupos de covariables se incluyen completos y los target son de la base de COVID19

def calculate_epsilon(dbs=['inegi2020'], target_filter={'variable_id__in': [2, 3], 
                                                               'date_occurrence__lte': '2020-03-31',
                                                               'date_occurrence__gte': '2020-03-01'}, mesh='mun'):
    '''
    '''
    dict_results = {
                    'node': [],
                    'id': [],
                    'variable': [], 
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
    
    N = CellState.objects.aggregate(Sum('pobtot'))['pobtot__sum']
    cells = get_mesh(mesh)

    map_cells_pobtot = {}

    for cell in cells:
        map_cells_pobtot[getattr(cell, 'gridid_' + mesh)] = cell.pobtot

    target_filter = mesh_occurrence_condition(mesh, target_filter)
    target_by_cell = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    map_cell_target = {}

    for tc in target_by_cell:
        map_cell_target[tc['gridid_' + mesh]] = tc['tcount']

    ## Nc
    Nc = 0
    for k in map_cell_target.keys():
        Nc += map_cell_target[k]

    ## PC
    PC = Nc/N

    ## Nc_
    Nc_ = N - Nc

    ## P_C
    P_C = (N-Nc)/N

    ## s0
    s0= np.log(PC/P_C)

    ## alpha
    alpha = 0.01

    for db in dbs:
        
        if db == 'inegi2020':
            covars = VariableINEGI2020.objects.all().using(db)

        for covar in covars:

            ## node
            dict_results['node'].append(db)

            ## id
            dict_results['id'].append(covar.id)            

            ## variable
            if db == 'inegi2020':
                dict_results['variable'].append(VariableINEGI2020Serializer(covar).data)

            ## Nx && Ncx
            Nx = 0
            Ncx = 0
            cells_presence = getattr(covar, 'cells_' + mesh)

            for gridid in cells_presence:
                Nx += map_cells_pobtot[gridid]

                if gridid in map_cell_target.keys():
                    Ncx += map_cell_target[gridid]

            dict_results['Nx'].append(Nx)
            dict_results['Ncx'].append(Ncx)

            ## PCX
            
            if Nx == 0:
                PCX = 0
            else:
                PCX = Ncx/Nx
            
            dict_results['PCX'].append(PCX)
            dict_results['PC'].append(PC)
            dict_results['Nc'].append(Nc)
            dict_results['N'].append(N)

            ## epsilon
            if Nx == 0:
                epsilon = 0
            else:
                epsilon = (Nx*(PCX - PC))/ ((Nx*PC*(1 - PC))**0.5)

            dict_results['epsilon'].append(epsilon)

            dict_results['Nc_'].append(Nc_)

            ## Nc_x
            Nc_x = Nx - Ncx
            dict_results['Nc_x'].append(Nc_x)

            dict_results['P_C'].append(P_C)

            ## P_CX
            if Nx == 0:
                P_CX = 1
            else:
                P_CX = Nc_x/Nx

            dict_results['P_CX'].append(P_CX)

            dict_results['s0'].append(s0)

            ## score
            score = np.log((Ncx/Nc + alpha)/(Nc_x/Nc_ + 2*alpha))
            dict_results['score'].append(score)

    return dict_results


def calculate_score(dbs=['inegi2020'],  mesh='mun', target='CONFIRMADO',
                    lim_inf_training='2020-03-01', lim_sup_training='2020-03-31', 
                    lim_inf_first=None, lim_sup_first=None, lim_inf_validation=None, lim_sup_validation=None):
    '''
    '''


    if lim_inf_first != None and lim_sup_first != None:
        target_filter_first = get_target_filter(mesh, lim_inf_first, lim_sup_first, target)
        target_first = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter_first).annotate(tcount=Count('id'))
        map_target_first = make_map(target_first, 'gridid_' + mesh, 'tcount')

        epsilon = calculate_epsilon(dbs, target_filter_first, mesh)
        s0_first = epsilon['s0'][0]
        df_epsilon_first = pd.DataFrame(epsilon)
    else:
        map_target_first = None
        s0_first = 0

    if lim_inf_validation != None and lim_sup_validation != None:
        target_filter_validation = get_target_filter(mesh, lim_inf_validation, lim_sup_validation, target)
        target_validation = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter_validation).annotate(tcount=Count('id'))
        map_target_validation = make_map(target_validation, 'gridid_' + mesh, 'tcount')
    else:
        map_target_validation = None

    map_cell_score = {}
    target_filter = get_target_filter(mesh, lim_inf_training, lim_sup_training, target)
    epsilon = calculate_epsilon(dbs, target_filter, mesh)
    s0 = epsilon['s0'][0]
    df_epsilon = pd.DataFrame(epsilon)
    cells = get_mesh(mesh)
    percentiles = 20

    target_training = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    map_target_training = make_map(target_training, 'gridid_' + mesh, 'tcount')

    for cell in cells:
        gridid = getattr(cell, 'gridid_'  + mesh)
        map_cell_score[gridid] = {'score_training': s0, 'gridid': gridid, 'pobtot': cell.pobtot}
        map_cell_score[gridid]['cell'] = get_serialized_cell(cell, mesh)

        if gridid in map_target_training.keys():
                map_cell_score[gridid]['cases_training'] = map_target_training[gridid]
        else:
            map_cell_score[gridid]['cases_training'] = 0

        if map_target_first != None:
            if gridid in map_target_first.keys():
                map_cell_score[gridid]['cases_first'] = map_target_first[gridid]
            else:
                map_cell_score[gridid]['cases_first'] = 0

            map_cell_score[gridid]['score_first'] = s0_first

        if map_target_validation != None:
            if gridid in map_target_validation.keys():
                map_cell_score[gridid]['cases_validation'] = map_target_validation[gridid]
            else:
                map_cell_score[gridid]['cases_validation'] = 0


    for db in dbs:
        
        if db == 'inegi2020':
            covars = VariableINEGI2020.objects.all().using(db)

        for covar in covars:

            cells_presence = getattr(covar, 'cells_' + mesh)
            current_score = df_epsilon[(df_epsilon.node == db) & (df_epsilon.id == covar.id)].iloc[0].score
            
            if map_target_first != None:
                current_score_first = df_epsilon_first[(df_epsilon_first.node == db) & (df_epsilon_first.id == covar.id)].iloc[0].score
            else:
                current_score_first = 0       

            for gridid in cells_presence:

                map_cell_score[gridid]['score_training'] += current_score

                if map_target_first != None:
                    map_cell_score[gridid]['score_first'] += current_score_first                    

    df_cells = pd.DataFrame(map_cell_score.values())
    N = df_cells.pobtot.sum()
    percentil_length = N / percentiles
    
    if map_target_first != None:

        df_cells = df_cells.sort_values('score_first', ascending=False)
        df_cells = df_cells.reset_index(drop=True)
        p_first = []
        percentil_first = []
        aux_first = 0

        cummulated_length = 0
        for d in range(percentiles):
            lower_first = aux_first
            upper_first = aux_first
            while cummulated_length < (d+1)*percentil_length:
                cummulated_length += df_cells.iloc[upper_first].pobtot
                upper_first += 1
            aux_first = upper_first

            cases_percentil_first = df_cells.iloc[lower_first:upper_first].cases_first.sum()
            pobtot_percentil_first = df_cells.iloc[lower_first:upper_first].pobtot.sum()

            p_first += [cases_percentil_first/pobtot_percentil_first for i in range(upper_first - lower_first)]
            percentil_first += [percentiles - d for i in range(upper_first - lower_first)]

        #print(len(p), len(percentil))
        df_cells['p_first'] = pd.Series(p_first)
        df_cells['percentil_first'] = pd.Series(percentil_first)

    df_cells = df_cells.sort_values('score_training', ascending=False)
    df_cells = df_cells.reset_index(drop=True)

    p_training = []
    percentil_training = []
    aux_training = 0

    cummulated_length = 0
    for d in range(percentiles):
        lower_training = aux_training
        upper_training = aux_training
        while cummulated_length < (d+1)*percentil_length:
            cummulated_length += df_cells.iloc[upper_training].pobtot
            upper_training += 1
        aux_training = upper_training

        cases_percentil_training = df_cells.iloc[lower_training:upper_training].cases_training.sum()
        pobtot_percentil_training = df_cells.iloc[lower_training:upper_training].pobtot.sum()

        p_training += [cases_percentil_training/pobtot_percentil_training for i in range(upper_training - lower_training)]
        percentil_training += [percentiles - d for i in range(upper_training - lower_training)]

    #print(len(p), len(percentil))
    df_cells['p_training'] = pd.Series(p_training)
    df_cells['percentil_training'] = pd.Series(percentil_training)

    if map_target_first != None:
        scores = np.array((df_cells['score_training'] - df_cells['score_first']).tolist())
        probas = np.array((df_cells['p_training'] - df_cells['p_first']).tolist())

        reg = LinearRegression()
        reg.fit(scores.reshape(-1, 1), probas)

        p_predicted_validation = reg.predict(scores.reshape(-1, 1))
        df_cells['p_predicted_validation'] = df_cells['p_training'] + pd.Series(p_predicted_validation)

        df_cells['cases_predicted_validation'] = (df_cells['pobtot'] - df_cells['cases_training'])*df_cells['p_predicted_validation']

    return df_cells.to_dict(orient='records')


def get_target_filter(mesh, lim_inf, lim_sup, target):
    '''
    '''
    target_filter = {}
    
    target_filter = mesh_occurrence_condition(mesh, target_filter)

    if target == 'CONFIRMADO' or target == 'FALLECIDO':
        target_filter['variable_id__in'] = [2, 3]
    elif target == 'NEGATIVO':
        target_filter['variable_id__in'] = [5]
    elif target == 'PRUEBA':
        target_filter['variable_id__in'] = [1, 2, 3]

    if target == 'FALLECIDO':
        if lim_inf != -99999:
            target_filter['fecha_def__gte'] = lim_inf
        
        if lim_sup != -99999:
            target_filter['fecha_def__lte'] = lim_sup
    else:
        if lim_inf != -99999:
            target_filter['date_occurrence__gte'] = lim_inf
        
        if lim_sup != -99999:
            target_filter['date_occurrence__lte'] = lim_sup

    return target_filter
