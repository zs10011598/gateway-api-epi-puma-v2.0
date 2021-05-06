from ..models.cell import *
from django.db.models import Sum, Count
from ..models.variable import *
from ..serializers.variable import *
from .helpers import *
from ..models.occurrence import *
import numpy as np
import pandas as pd
from ..serializers.cell import *

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
    target_by_cell = Occurrence.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
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


def calculate_score(dbs=['inegi2020'], target_filter={ 'variable_id__in': [2, 3], 
                                                       'date_occurrence__lte': '2020-03-31',
                                                       'date_occurrence__gte': '2020-03-01'}, mesh='mun'):
    '''
    '''
    map_cell_score = {}
    epsilon = calculate_epsilon(dbs, target_filter, mesh)
    s0 = epsilon['s0'][0]
    df_epsilon = pd.DataFrame(epsilon)
    cells = get_mesh(mesh)

    for cell in cells:
        map_cell_score[getattr(cell, 'gridid_'  + mesh)] = {'score': s0, 'gridid': getattr(cell, 'gridid_'  + mesh)}
        map_cell_score[getattr(cell, 'gridid_'  + mesh)]['cell'] = get_serialized_cell(cell, mesh)

    for db in dbs:
        
        if db == 'inegi2020':
            covars = VariableINEGI2020.objects.all().using(db)

        for covar in covars:

            current_score = df_epsilon[(df_epsilon.node == db) & (df_epsilon.id == covar.id)].iloc[0].score
            cells_presence = getattr(covar, 'cells_' + mesh)
            
            for gridid in cells_presence:

                if gridid in map_cell_score.keys():
                    map_cell_score[gridid]['score'] += current_score
                else:
                    map_cell_score[gridid]['score'] = current_score

                #if db == 'inegi2020':
                #    map_cell_score[gridid]['covars'].append({'name': covar.name + ' ' + covar.interval, 'score': current_score})

    return map_cell_score.values()