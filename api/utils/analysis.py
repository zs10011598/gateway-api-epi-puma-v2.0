from .helpers import *
from ..models.occurrence import *
from ..models.variable import *
from ..serializers.variable import *
from ..serializers.occurrence import *
from django.db.models import Count, Sum
import numpy as np
import pandas as pd


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


def calculate_epsilon_cells_ensamble(
    covariables, 
    covariable_filter, 
    occs,
    mesh):
    
    taxon_map_name_snib = {
        'kingdom': 'reinovalido', 
        'phylum': 'phylumdivisionvalido', 
        'class': 'clasevalida', 
        'order': 'ordenvalido', 
        'family': 'familiavalida', 
        'genus': 'generovalido', 
        'species': 'especievalida'
    }

    variables_occs = []
    data = []

    try:
        for cov in covariables:
            cov_occs = []
            if cov in covariable_filter.keys():
                for cov_filter in covariable_filter[cov]:
                    target_cov = {}
                    if cov == 'inegi2020':
                        target_cov = {cov_filter['taxon']: cov_filter['value']}
                        variables = VariableINEGI2020\
                            .objects\
                            .using(cov)\
                            .values()\
                            .filter(**target_cov)
                    elif cov == 'snib':
                        target_cov = {
                            taxon_map_name_snib[cov_filter['taxon']]: cov_filter['value']}
                        variables = VariableSNIB\
                            .objects\
                            .using(cov)\
                            .values()\
                            .filter(**target_cov)
                    elif cov == 'worldclim':
                        target_cov = {
                            cov_filter['taxon']: cov_filter['value']}
                        variables = VariableWorldclim\
                            .objects\
                            .using(cov)\
                            .values()\
                            .filter(**target_cov)
                    #print(cov, target_cov)
                    cov_occs += variables
            else:
                if cov == 'inegi2020':
                    cov_occs = VariableINEGI2020.objects.using(cov).all()
                elif cov == 'snib':
                    cov_occs = VariableSNIB.objects.using(cov).all()
                elif cov == 'worldclim':
                    cov_occs = VariableWorldclim.objects.using(cov).all()

            for co_item in cov_occs:
                co_item['node'] = cov 

            variables_occs += cov_occs
    except Exception as e:
        print(str(e))
        return (None, str(e))

    # DEBUG
    #for vc in variables_occs:
    #    if vc['especievalida'].startswith('Alouatta palliata'):
    #       print(vc['especievalida'], vc['cells_' + mesh])

    dict_results = {
        'group_name': [],
        "reinovalido": [],
        "phylumdivisionvalido": [],
        "clasevalida": [],
        "ordenvalido": [],
        "familiavalida": [],
        "generovalido": [],
        "especieepiteto": [],
        "nombreinfra": [],
        'especievalida': [],
        "type": [],
        "label": [],
        "layer": [],
        "bid": [],
        "icat": [],
        "tag": [],
        "unidad": [],
        "coeficiente": [],
        "cells":[],
        "tipo": [],
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
        'score':[],
    }

    cells = get_mesh(mesh)
    N = cells.count()
    Nc = len(occs)
    PC = Nc/N
    Nc_ = N - Nc
    P_C = (N-Nc)/N
    s0= np.log(PC/P_C)
    alpha = 0.01

    for variable in variables_occs:

        if len(variable['cells_' + mesh]) == 0:
            continue

        dict_results['group_name'].append(variable['node'])
        
        if variable['node'] == 'inegi2020':
            #print(variable.keys())
            dict_results['reinovalido'].append('')    
            dict_results['phylumdivisionvalido'].append('')
            dict_results['clasevalida'].append('')
            dict_results['ordenvalido'].append('')
            dict_results['familiavalida'].append('')
            dict_results['generovalido'].append('')
            dict_results['especieepiteto'].append('')
            dict_results['nombreinfra'].append('')
            dict_results['type'].append('2')
            dict_results['label'].append(variable['name'])
            dict_results['layer'].append(variable['code'])
            dict_results['bid'].append(variable['id'])
            dict_results['icat'].append(variable['bin'])
            dict_results['tag'].append(variable['interval'])
            dict_results['unidad'].append('')
            dict_results['coeficiente'].append('')
            dict_results['tipo'].append('1')
            dict_results['especievalida'].append(variable['name'] + ' ' + variable['interval'])
        elif variable['node'] == 'snib':
            dict_results['reinovalido'].append(variable['reinovalido'])
            dict_results['phylumdivisionvalido'].append(variable['phylumdivisionvalido'])
            dict_results['clasevalida'].append(variable['clasevalida'])
            dict_results['ordenvalido'].append(variable['ordenvalido'])
            dict_results['familiavalida'].append(variable['familiavalida'])
            dict_results['generovalido'].append(variable['generovalido'])
            dict_results['especieepiteto'].append(variable['especievalida']\
                .split(' ')[1] if variable['especievalida'] != None else variable['especievalida'])
            dict_results['nombreinfra'].append('')
            dict_results['type'].append('0')
            dict_results['label'].append('')
            dict_results['layer'].append('')
            dict_results['bid'].append('')
            dict_results['icat'].append('')
            dict_results['tag'].append('')
            dict_results['unidad'].append('')
            dict_results['coeficiente'].append('')
            dict_results['tipo'].append('0')
            dict_results['especievalida'].append(variable['especievalida'])
        elif variable['node'] == 'worldclim':
            #print(variable.keys())
            dict_results['reinovalido'].append('')
            dict_results['phylumdivisionvalido'].append('')
            dict_results['clasevalida'].append('')
            dict_results['ordenvalido'].append('')
            dict_results['familiavalida'].append('')
            dict_results['generovalido'].append('')
            dict_results['especieepiteto'].append('')
            dict_results['nombreinfra'].append('')
            dict_results['type'].append('1')
            dict_results['label'].append(variable['label'])
            dict_results['layer'].append(variable['layer'])
            dict_results['bid'].append(variable['id'])
            dict_results['icat'].append(variable['icat'])
            dict_results['tag'].append(variable['interval'])
            dict_results['unidad'].append('')
            dict_results['coeficiente'].append('')
            dict_results['tipo'].append('1')
            dict_results['especievalida'].append(variable['label'] + ' ' + variable['interval'])
        
        dict_results['cells'].append(variable['cells_' + mesh])
        target_cells = list(set([occ['gridid_' + mesh] for occ in occs]))

        Nx = len(variable['cells_' + mesh])
        Ncx = len([cell for cell in target_cells if cell in variable['cells_' + mesh]])
        dict_results['Nx'].append(Nx)
        dict_results['Ncx'].append(Ncx)

        if Nx == 0:
            PCX = 0
        else:
            PCX = Ncx/Nx
        
        dict_results['PCX'].append(PCX)
        dict_results['PC'].append(PC)
        dict_results['Nc'].append(Nc)
        dict_results['N'].append(N)

        if Nx == 0:
            epsilon = 0
        else:
            epsilon = (Nx*(PCX - PC))/ ((Nx*PC*(1 - PC))**0.5)

        dict_results['epsilon'].append(epsilon)
        dict_results['Nc_'].append(Nc_)
        Nc_x = Nx - Ncx
        dict_results['Nc_x'].append(Nc_x)
        dict_results['P_C'].append(P_C)
        if Nx == 0:
            P_CX = 1
        else:
            P_CX = Nc_x/Nx
        dict_results['P_CX'].append(P_CX)
        dict_results['s0'].append(s0)
        #score = np.log((Ncx/Nc + alpha)/(Nc_x/Nc_ + 2*alpha))
        score = np.log(((Ncx + 0.005)/(Nc + 0.01))/((Nc_x + 0.01)/(Nc_+0.005)))
        dict_results['score'].append(score)

    #print(dict_results)
    M = len(dict_results['group_name'])
    return ([
                {
                    'group_name': dict_results['group_name'][i],
                    "reinovalido": dict_results['reinovalido'][i],
                    "phylumdivisionvalido": dict_results['phylumdivisionvalido'][i],
                    "clasevalida": dict_results['clasevalida'][i],
                    "ordenvalido": dict_results['ordenvalido'][i],
                    "familiavalida": dict_results['familiavalida'][i],
                    "generovalido": dict_results['generovalido'][i],
                    "especieepiteto": dict_results['especieepiteto'][i],
                    "nombreinfra": dict_results['nombreinfra'][i],
                    "especievalida": dict_results['especievalida'][i],
                    "type": dict_results['type'][i],
                    "label": dict_results['label'][i],
                    "layer": dict_results['layer'][i],
                    "bid": dict_results['bid'][i],
                    "icat": dict_results['icat'][i],
                    "tag": dict_results['tag'][i],
                    "unidad": dict_results['unidad'][i],
                    "coeficiente": dict_results['coeficiente'][i],
                    "cells":dict_results['cells'][i],
                    "tipo": dict_results['tipo'][i],
                    'ni': dict_results['Nc'][i], 
                    'nj': dict_results['Nx'][i], 
                    'nij': dict_results['Ncx'][i], 
                    'n': dict_results['N'][i], 
                    'epsilon': dict_results['epsilon'][i],
                    'score': dict_results['score'][i],
                    'biotic': True if dict_results['tipo'][i] == '0' else False} for i in range(M)], None)


def calculate_score_cells_ensamble(data):
    score_cells = {}
    for cov in data:
        for cell in cov['cells']:
            if cell in score_cells.keys():
                score_cells[cell]['tscore'] += cov['score']
            else:
                score_cells[cell] = {'gridid': cell, 'tscore': cov['score']}
    return score_cells.values()


def validation_data_analysis(mesh, occs_valid, data_score_cell):
    validation_data = []
    
    cells_df = pd.DataFrame(data_score_cell)
    cells_df = cells_df.sort_values('tscore', ascending=False)
    N = cells_df.shape[0]
    
    cells_sample_df = pd.DataFrame([occ for occ in occs_valid])
    cells_sample_df = cells_sample_df.rename(columns={'gridid_' + mesh: 'gridid'})
    cells_sample_df = cells_sample_df.drop(columns=['tcount'])
    N_sample = cells_sample_df.shape[0]
    cells_sample_df['sample'] = pd.Series([1 for i in range(N_sample)])

    cells_df = cells_df.merge(cells_sample_df, on='gridid', how='left')
    cells_df = cells_df.reset_index(drop=True)
    cells_df['sample'] = cells_df['sample'].fillna(0)

    #print(cells_df['sample'].sum())
    dd = cells_sample_df[~(cells_sample_df['gridid'].isin(cells_df['gridid'].tolist()))]
    #print(dd)
    nulls = dd['gridid'].tolist()
    #print(nulls)
    nulls = len(nulls)

    length_bin = N/10
    for i in range(10):
        vp = cells_df.iloc[0:int((i+1)*length_bin)]['sample'].sum()
        fn = N_sample - vp - nulls
        validation_data.append({
                'decil': 10 - i,
                'vp': vp, 
                'fn': fn,
                'nulo': nulls,
                'recall': vp/(vp+fn)
            })        

    return validation_data


def caculate_decil_info(data, data_score_cell, deciles):
    percentage_avg = []
    cells_df = pd.DataFrame(data_score_cell)
    cells_df = cells_df.sort_values('tscore', ascending=False)
    length_bin = int(cells_df.shape[0]/10)

    for decil in deciles:
        cells_decile = cells_df.iloc[length_bin*(10-decil): length_bin*(10-decil+1)]['gridid'].tolist()
        N = len(cells_decile)

        for cov in data:

            #print(cells_decile)
            #print(cov['cells'])
            cells_cov_decile = len([cell for cell in cov['cells'] if cell in cells_decile])
            if cov['nj'] != 0 and cells_cov_decile != 0:
                occ = round(cells_cov_decile/float(cov['nj'])*100, 3)
                occ_perdecile = round(cells_cov_decile/float(N)*100, 3)
                percentage_avg.append({
                    "decil": decil,
                    "species": cov['especievalida'] if cov['tipo'] == "0" else cov['label'] + ' ' + cov['tag'],
                    "epsilon": cov['epsilon'],
                    "score": cov['score'],
                    "occ": occ,
                    "occ_perdecile": occ_perdecile
                })
            else:
                #print(cov['generovalido'] + ' ' + cov['especieepiteto'] if cov['tipo'] == "0" else cov['label'] + ' ' + cov['tag'])
                #print(N, cov['nj'], cells_cov_decile)
                pass

    return percentage_avg