from .helpers import get_mesh, get_demographic, mesh_occurrence_condition
from ..models.occurrence import *
from ..serializers.variable import *
from django.db.models import Count
import numpy as np


def calculate_epsilon(dbs=['inegi2020'], target_filter={'variable_id__in': [2, 3], 
                                                        'date_occurrence__lte': '2020-03-31',
                                                        'date_occurrence__gte': '2020-03-01'}, 
                      mesh='mun', target='CONFIRMADO', demographic_group=None):
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
    
    cells = get_mesh(mesh)
    N = cells.count()

    demographic_group_dict = {}

    if demographic_group != None:
        demographic_group_dict = get_demographic(mesh, demographic_group)

    map_cells_pobtot = {}

    for cell in cells:
        gridid = getattr(cell, 'gridid_' + mesh)
        if demographic_group != None:
            map_cells_pobtot[gridid] = demographic_group_dict[gridid]
        else:
            map_cells_pobtot[gridid] = cell.pobtot

    target_filter = mesh_occurrence_condition(mesh, target_filter)

    if target == 'VACUNADO':
        cases_by_cell = OccurrenceVaccines.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    else:
        cases_by_cell = OccurrenceVaccines.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))

    print('cases_by_cell = ', cases_by_cell)    

    target_by_cell = []
    map_cases_by_cell = {}
    for cbc in cases_by_cell:
        target_by_cell.append({'gridid_' + mesh: cbc['gridid_' + mesh]}) 
        map_cases_by_cell[cbc['gridid_' + mesh]] = cbc['tcount']

    print('target_by_cell = ', target_by_cell)

    map_cell_target = {}
    for tc in target_by_cell:
        map_cell_target[tc['gridid_' + mesh]] = 1

    print('map_cell_target = ', map_cell_target)

    ## Nc
    Nc = 0
    for k in map_cell_target.keys():
        Nc += map_cell_target[k]
    print('Nc = ' , Nc)

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
            #score = np.log((Ncx/Nc + alpha)/(Nc_x/Nc_ + 2*alpha))
            score = np.log(((Ncx + 0.005)/(Nc + 0.01))/((Nc_x + 0.01)/(Nc_+0.005)))
            dict_results['score'].append(score)

    return dict_results