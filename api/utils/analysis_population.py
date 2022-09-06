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

### Por el momento los grupos de covariables se incluyen completos y los target son de la base de COVID19

def calculate_epsilon(dbs=['inegi2020'], covariable_filter={}, target_filter={'variable_id__in': [2, 3], 
                                                        'date_occurrence__lte': '2020-03-31',
                                                        'date_occurrence__gte': '2020-03-01'}, 
                      mesh='mun', target='CONFIRMADO', demographic_group=None, 
                      covariable_modifier=None, covars_cells=False):
    '''
    '''
    covar_cells_relation = {} 
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
                    'score':[],
                    }

    if covars_cells:
        dict_results['covars'] = []

    demographic_group_dict = {}

    if demographic_group != None:
        demographic_group_dict = get_demographic(mesh, demographic_group)

        N = 0
        for gridid in demographic_group_dict.keys():
            N += demographic_group_dict[gridid]

        #print(demographic_group_dict)

    else:
        N = CellState.objects.aggregate(Sum('pobtot'))['pobtot__sum']
    
    cells = get_mesh(mesh)

    map_cells_pobtot = {}

    for cell in cells:
        gridid = getattr(cell, 'gridid_' + mesh)
        if demographic_group != None:
            map_cells_pobtot[gridid] = demographic_group_dict[gridid]
        else:
            map_cells_pobtot[gridid] = cell.pobtot


    target_filter = mesh_occurrence_condition(mesh, target_filter)
    #print(mesh, target_filter)

    if target == 'VACUNADO':
        target_by_cell = OccurrenceVaccines.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    else:
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
            """
                First type of analysis, static covariables
            """
            covars = VariableINEGI2020.objects.all().using(db)
            #print(covars)

        if db == 'irag':
            """
                Second type of analysis, dynamical covariables
            """
            covars = []
            filter_names = []

            lim_sup_training = target_filter['date_occurrence__lte'] if 'date_occurrence__lte' in target_filter.keys() else target_filter['fecha_def__lte']
            lim_inf_training = target_filter['date_occurrence__gte'] if 'date_occurrence__gte' in target_filter.keys() else target_filter['fecha_def__gte']


            for backward_period in range(1, 4):
                
                ## Filtering covars by name
                if db in covariable_filter.keys():
                    filter_names = covariable_filter[db]
                    covars_to_dicretize = VariableIRAG.objects.using('irag').filter(name__in=filter_names)
                else:
                    covars_to_dicretize = VariableIRAG.objects.all().using('irag')

                #print('No. covars ' + str(covars_to_dicretize.count()))

                delta_months = dt.timedelta(days = -backward_period*30)

                lim_sup_training_bp = dt.datetime.strptime(lim_sup_training, '%Y-%m-%d') + delta_months
                lim_inf_training_bp = dt.datetime.strptime(lim_inf_training, '%Y-%m-%d') + delta_months

                lim_sup_training_bp = lim_sup_training_bp.strftime("%Y-%m-%d")
                lim_inf_training_bp = lim_inf_training_bp.strftime("%Y-%m-%d")
                
                #print('HISTORICAL DYNAMICAL VARIABLES PERIOD ' + str(backward_period) + ' DE ' + lim_inf_training_bp + ' A ' + lim_sup_training_bp)

                ## Filtering occs by date and name
                if db in covariable_filter.keys():
                    filter_names = covariable_filter[db]
                    occs = OccurrenceIRAG.objects.using('irag').filter(date_occurrence__lte=lim_sup_training_bp, 
                                                                        date_occurrence__gte=lim_inf_training_bp, 
                                                                        var__in=filter_names)
                else:
                    occs = OccurrenceIRAG.objects.using('irag').filter(date_occurrence__lte=lim_sup_training_bp, 
                                                                        date_occurrence__gte=lim_inf_training_bp)
                covars += get_discretized_covars(occs, covars_to_dicretize, mesh, backward_period)

            covars += get_historical_modified_variables(mesh, covars)

        if db == 'covid19':
            """
                Third type of analysis, target covariables as dynamical covariables
            """
            lim_sup_training = target_filter['date_occurrence__lte'] if 'date_occurrence__lte' in target_filter.keys() else target_filter['fecha_def__lte']
            lim_inf_training = target_filter['date_occurrence__gte'] if 'date_occurrence__gte' in target_filter.keys() else target_filter['fecha_def__gte']
            covars = []

            if covariable_filter == None or not db in covariable_filter.keys():
                pass                
            else:
                if db in covariable_filter.keys():

                    derivatives_covars = []

                    for covar in covariable_filter[db]:

                        # historical variables
                        for backward_period in range(4):
                            
                            delta_months = dt.timedelta(days = -backward_period*30)
                            lim_sup_training_bp = dt.datetime.strptime(lim_sup_training, '%Y-%m-%d') + delta_months
                            lim_inf_training_bp = dt.datetime.strptime(lim_inf_training, '%Y-%m-%d') + delta_months
                            lim_sup_training_bp = lim_sup_training_bp.strftime("%Y-%m-%d")
                            lim_inf_training_bp = lim_inf_training_bp.strftime("%Y-%m-%d")

                            covar_filter_bp = get_covar_filter(mesh, lim_inf_training_bp, lim_sup_training_bp, covar)
                            occs = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**covar_filter_bp).annotate(tcount=Count('id')).order_by('-tcount')
                            modifier = covariable_modifier[db][covar]
                            generated_covars = get_modified_variables(occs, mesh, covar, modifier, 10, map_cells_pobtot, backward_period)
    
                            covars += generated_covars

                            # derivatives 
                            delta_months = dt.timedelta(days = -(backward_period + 1)*30)
                            lim_sup_training_dbp = dt.datetime.strptime(lim_sup_training_bp, '%Y-%m-%d') + delta_months
                            lim_inf_training_dbp = dt.datetime.strptime(lim_inf_training_bp, '%Y-%m-%d') + delta_months
                            lim_sup_training_dbp = lim_sup_training_dbp.strftime("%Y-%m-%d")
                            lim_inf_training_dbp = lim_inf_training_dbp.strftime("%Y-%m-%d")

                            covar_filter_dbp = get_covar_filter(mesh, lim_inf_training_dbp, lim_sup_training_dbp, covar)
                            occs_d = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**covar_filter_dbp).annotate(tcount=Count('id')).order_by('-tcount')

                            d_occs = []
                            for gridid in map_cells_pobtot.keys():
                                tcount = 0
                                for node in occs:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount = node['tcount']
                                        break
                                for node in occs_d:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount -= node['tcount']
                                        break
                                d_occs.append({'gridid_' + mesh: gridid, 'tcount': tcount})

                            d_occs.sort(key=lambda x: x['tcount'], reverse=True)
                            generated_covars_d = get_modified_variables(d_occs, mesh, covar, modifier, 10, map_cells_pobtot, str(backward_period), 'D')
                            derivatives_covars += generated_covars_d

                            # Second derivatives

                            delta_months = dt.timedelta(days = -(backward_period + 2)*30)
                            lim_sup_training_d2bp = dt.datetime.strptime(lim_sup_training_bp, '%Y-%m-%d') + delta_months
                            lim_inf_training_d2bp = dt.datetime.strptime(lim_inf_training_bp, '%Y-%m-%d') + delta_months
                            lim_sup_training_d2bp = lim_sup_training_d2bp.strftime("%Y-%m-%d")
                            lim_inf_training_d2bp = lim_inf_training_d2bp.strftime("%Y-%m-%d")

                            covar_filter_d2bp = get_covar_filter(mesh, lim_inf_training_d2bp, lim_sup_training_d2bp, covar)
                            occs_d2 = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**covar_filter_d2bp).annotate(tcount=Count('id')).order_by('-tcount')

                            d2_occs = []
                            for gridid in map_cells_pobtot.keys():
                                tcount = 0
                                for node in occs:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount = node['tcount']
                                        break
                                for node in occs_d:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount -= 2*node['tcount']
                                        break
                                for node in occs_d2:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount += node['tcount']
                                        break
                                d2_occs.append({'gridid_' + mesh: gridid, 'tcount': tcount})

                            d2_occs.sort(key=lambda x: x['tcount'], reverse=True)
                            generated_covars_d2 = get_modified_variables(d2_occs, mesh, covar, modifier, 10, map_cells_pobtot, str(backward_period), 'D^2')
                            derivatives_covars += generated_covars_d2

                        generated_covars_d3 = get_historical_modified_variables(mesh, covars)

                        covars += generated_covars_d3

                    covars += derivatives_covars


                    #print(covars)

                else:
                    covars = []

        for gc in covars:
            covar_cells_relation[gc.id] = gc.cells_mun

        with open('./covar_cells/covar_cells_relation{0}.json'.format(db), 'w') as f:
            f.write(json.dumps(covar_cells_relation))

        for covar in covars:

            ## node
            dict_results['node'].append(db)

            ## id
            print(covar)
            dict_results['id'].append(covar.id)            

            ## variable
            if db == 'inegi2020':
                dict_results['variable'].append(VariableINEGI2020Serializer(covar).data)

            if db == 'irag':
                #print(covar)
                dict_results['variable'].append(VariableSerializer(covar).data)
                #print(VariableSerializer(covar).data)

            if db == 'covid19':
                print(covar)
                dict_results['variable'].append(VariableSerializer(covar).data)

            ## Nx && Ncx
            Nx = 0
            Ncx = 0
            cells_presence = getattr(covar, 'cells_' + mesh)
            #print('COVAR => ', covar.name, '; bin => ', covar.bin, '; no. cells: ', len(cells_presence))

            for gridid in cells_presence:
                Nx += map_cells_pobtot[gridid] if gridid in map_cells_pobtot.keys() else 0

                if gridid in map_cell_target.keys():
                    Ncx += map_cell_target[gridid] if gridid in map_cell_target.keys() else 0

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

            #print('Nx => ', Nx)
            #print('PC => ', PC)

            ## epsilon
            if Nx == 0 or PC == 0:
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

            if covars_cells:

                covar_cells_item = {}
                
                for covar in covars:
                    covar_cells_item['id'] = covar.id
                    #covar_cells_item['name'] = covar.name
                    covar_cells_item['db'] = db
                    covar_cells_item['cells_' + mesh] = getattr(covar, 'cells_' + mesh)
                    covar_cells_item['score'] = score
                    
                    dict_results['covars'].append(covar_cells_item)

    if covars_cells:
        return {'covars': dict_results['covars']}

    return dict_results


def calculate_score(dbs=['inegi2020'], covariable_filter={}, mesh='mun', target='CONFIRMADO',
                    lim_inf_training='2020-03-01', lim_sup_training='2020-03-31', 
                    lim_inf_first=None, lim_sup_first=None, lim_inf_validation=None, 
                    lim_sup_validation=None, demographic_group=None, attribute_filter=None,
                    covariable_modifier=None, epsilon_threshold=None):
    '''
    '''
    demographic_group_dict = {}
    if demographic_group != None:
        demographic_group_dict = get_demographic(mesh, demographic_group)

    cells = get_mesh(mesh)
    map_cells_pobtot = {}
    for cell in cells:
        gridid = getattr(cell, 'gridid_' + mesh)
        if demographic_group != None:
            map_cells_pobtot[gridid] = demographic_group_dict[gridid]
        else:
            map_cells_pobtot[gridid] = cell.pobtot

    if lim_inf_first != None and lim_sup_first != None:
        target_filter_first = get_target_filter(mesh, lim_inf_first, lim_sup_first, target, attribute_filter)
        print(target_filter_first)

        if target == 'VACUNADO':
            target_first = OccurrenceCOVID19.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter_first).annotate(tcount=Count('id'))
        else:
            target_first = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter_first).annotate(tcount=Count('id'))

        map_target_first = make_map(target_first, 'gridid_' + mesh, 'tcount')

        epsilon = calculate_epsilon(dbs, covariable_filter, target_filter_first, mesh, target, demographic_group, covariable_modifier, False)
        s0_first = epsilon['s0'][0]
        df_epsilon_first = pd.DataFrame(epsilon)
        if epsilon_threshold != None:
            df_epsilon_first = df_epsilon_first[(df_epsilon_first['epsilon'] >= epsilon_threshold) | (df_epsilon_first['epsilon'] <= -epsilon_threshold)]
    else:
        map_target_first = None
        s0_first = 0

    if lim_inf_validation != None and lim_sup_validation != None:
        target_filter_validation = get_target_filter(mesh, lim_inf_validation, lim_sup_validation, target, attribute_filter)

        if target == 'VACUNADO':
            target_validation = OccurrenceCOVID19.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter_validation).annotate(tcount=Count('id'))
        else:
            target_validation = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter_validation).annotate(tcount=Count('id'))
        
        map_target_validation = make_map(target_validation, 'gridid_' + mesh, 'tcount')
    else:
        map_target_validation = None

    map_cell_score = {}
    target_filter = get_target_filter(mesh, lim_inf_training, lim_sup_training, target, attribute_filter)
    epsilon = calculate_epsilon(dbs, covariable_filter, target_filter, mesh, target, demographic_group, covariable_modifier, False)
    s0 = epsilon['s0'][0]
    df_epsilon = pd.DataFrame(epsilon)
    if epsilon_threshold != None:
        df_epsilon = df_epsilon[(df_epsilon['epsilon'] >= epsilon_threshold) | (df_epsilon['epsilon'] <= -epsilon_threshold)]
    cells = get_mesh(mesh)
    percentiles = 20

    #print(df_epsilon.head(50))

    if target == 'VACUNADO':
        target_training = OccurrenceCOVID19.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    else:
        target_training = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))

    map_target_training = make_map(target_training, 'gridid_' + mesh, 'tcount')

    for cell in cells:
        gridid = getattr(cell, 'gridid_'  + mesh)
        map_cell_score[gridid] = {'score_training': s0, 'gridid': gridid, 'pobtot': cell.pobtot}
        map_cell_score[gridid]['cell'] = get_serialized_cell(cell, mesh)

        if demographic_group != None:
            map_cell_score[gridid][demographic_group] = demographic_group_dict[gridid]

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

        if db == 'irag':
            filter_names = []
            covars = []

            lim_sup_training = target_filter['date_occurrence__lte'] if 'date_occurrence__lte' in target_filter.keys() else target_filter['fecha_def__lte']
            lim_inf_training = target_filter['date_occurrence__gte'] if 'date_occurrence__gte' in target_filter.keys() else target_filter['fecha_def__gte']

            for backward_period in range(1, 4):

                ## Filtering covars by name
                if db in covariable_filter.keys():
                    filter_names = covariable_filter[db]
                    covars_to_dicretize = VariableIRAG.objects.using('irag').filter(name__in=filter_names)
                else:
                    covars_to_dicretize = VariableIRAG.objects.all().using('irag')

                #print('No. covars ' + str(len(covars)))

                delta_months = dt.timedelta(days = -backward_period*30)

                lim_sup_training_bp = dt.datetime.strptime(lim_sup_training, '%Y-%m-%d') + delta_months
                lim_inf_training_bp = dt.datetime.strptime(lim_inf_training, '%Y-%m-%d') + delta_months

                lim_sup_training_bp = lim_sup_training_bp.strftime("%Y-%m-%d")
                lim_inf_training_bp = lim_inf_training_bp.strftime("%Y-%m-%d")
                
                #print('HISTORICAL DYNAMICAL VARIABLES PERIOD ' + str(backward_period) + ' DE ' + lim_inf_training_bp + ' A ' + lim_sup_training_bp)

                ## Filtering occs by date and name
                if db in covariable_filter.keys():
                    filter_names = covariable_filter[db]
                    occs = OccurrenceIRAG.objects.using('irag').filter(date_occurrence__lte=lim_sup_training_bp, 
                                                                        date_occurrence__gte=lim_inf_training_bp, 
                                                                        var__in=filter_names)
                else:
                    occs = OccurrenceIRAG.objects.using('irag').filter(date_occurrence__lte=lim_sup_training_bp, 
                                                                        date_occurrence__gte=lim_inf_training_bp)
                covars += get_discretized_covars(occs, covars_to_dicretize, mesh, backward_period)

        if db == 'covid19':

            lim_sup_training = target_filter['date_occurrence__lte'] if 'date_occurrence__lte' in target_filter.keys() else target_filter['fecha_def__lte']
            lim_inf_training = target_filter['date_occurrence__gte'] if 'date_occurrence__gte' in target_filter.keys() else target_filter['fecha_def__gte']
            
            covars = []

            if covariable_filter == None or not db in covariable_filter.keys():
                pass                
            else:
                if db in covariable_filter.keys():

                    derivatives_covars = []

                    for covar in covariable_filter[db]:

                        for backward_period in range(4):
                            
                            delta_months = dt.timedelta(days = -backward_period*30)
                            lim_sup_training_bp = dt.datetime.strptime(lim_sup_training, '%Y-%m-%d') + delta_months
                            lim_inf_training_bp = dt.datetime.strptime(lim_inf_training, '%Y-%m-%d') + delta_months
                            lim_sup_training_bp = lim_sup_training_bp.strftime("%Y-%m-%d")
                            lim_inf_training_bp = lim_inf_training_bp.strftime("%Y-%m-%d")

                            covar_filter_bp = get_covar_filter(mesh, lim_inf_training_bp, lim_sup_training_bp, covar)
                            occs = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**covar_filter_bp).annotate(tcount=Count('id')).order_by('-tcount')
                            modifier = covariable_modifier[db][covar]
                            generated_covars = get_modified_variables(occs, mesh, covar, modifier, 10, map_cells_pobtot, backward_period)

                            covars += generated_covars

                            # derivatives 
                            delta_months = dt.timedelta(days = -(backward_period + 1)*30)
                            lim_sup_training_dbp = dt.datetime.strptime(lim_sup_training_bp, '%Y-%m-%d') + delta_months
                            lim_inf_training_dbp = dt.datetime.strptime(lim_inf_training_bp, '%Y-%m-%d') + delta_months
                            lim_sup_training_dbp = lim_sup_training_dbp.strftime("%Y-%m-%d")
                            lim_inf_training_dbp = lim_inf_training_dbp.strftime("%Y-%m-%d")

                            covar_filter_dbp = get_covar_filter(mesh, lim_inf_training_dbp, lim_sup_training_dbp, covar)
                            occs_d = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**covar_filter_dbp).annotate(tcount=Count('id')).order_by('-tcount')

                            d_occs = []
                            for gridid in map_cells_pobtot.keys():
                                tcount = 0
                                for node in occs:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount = node['tcount']
                                        break
                                for node in occs_d:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount -= node['tcount']
                                        break
                                d_occs.append({'gridid_' + mesh: gridid, 'tcount': tcount})

                            d_occs.sort(key=lambda x: x['tcount'], reverse=True)
                            generated_covars_d = get_modified_variables(d_occs, mesh, covar, modifier, 10, map_cells_pobtot, str(backward_period), 'D')
                            derivatives_covars += generated_covars_d

                            # Second derivatives

                            delta_months = dt.timedelta(days = -(backward_period + 2)*30)
                            lim_sup_training_d2bp = dt.datetime.strptime(lim_sup_training_bp, '%Y-%m-%d') + delta_months
                            lim_inf_training_d2bp = dt.datetime.strptime(lim_inf_training_bp, '%Y-%m-%d') + delta_months
                            lim_sup_training_d2bp = lim_sup_training_d2bp.strftime("%Y-%m-%d")
                            lim_inf_training_d2bp = lim_inf_training_d2bp.strftime("%Y-%m-%d")

                            covar_filter_d2bp = get_covar_filter(mesh, lim_inf_training_d2bp, lim_sup_training_d2bp, covar)
                            occs_d2 = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**covar_filter_d2bp).annotate(tcount=Count('id')).order_by('-tcount')

                            d2_occs = []
                            for gridid in map_cells_pobtot.keys():
                                tcount = 0
                                for node in occs:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount = node['tcount']
                                        break
                                for node in occs_d:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount -= 2*node['tcount']
                                        break
                                for node in occs_d2:
                                    if gridid == node['gridid_' + mesh]:
                                        tcount += node['tcount']
                                        break
                                d2_occs.append({'gridid_' + mesh: gridid, 'tcount': tcount})

                            d2_occs.sort(key=lambda x: x['tcount'], reverse=True)
                            generated_covars_d2 = get_modified_variables(d2_occs, mesh, covar, modifier, 10, map_cells_pobtot, str(backward_period), 'D^2')
                            derivatives_covars += generated_covars_d2

                        generated_covars_d3 = get_historical_modified_variables(mesh, covars)

                        covars += generated_covars_d3

                    covars += derivatives_covars

                else:
                    covars = []

        for covar in covars:

            cells_presence = getattr(covar, 'cells_' + mesh)
            
            if df_epsilon[(df_epsilon.node == db) & (df_epsilon.id == covar.id)].shape[0] > 0:
                current_score = df_epsilon[(df_epsilon.node == db) & (df_epsilon.id == covar.id)].iloc[0].score
            else:
                continue
            
            df_aux = df_epsilon_first[(df_epsilon_first.node == db) & (df_epsilon_first.id == covar.id)]
            if map_target_first != None and df_aux.shape[0] > 0:
                current_score_first = df_aux.iloc[0].score
            else:
                current_score_first = 0       

            for gridid in cells_presence:
                
                if gridid in map_cell_score.keys():
                    map_cell_score[gridid]['score_training'] += current_score
                    if gridid == '15121':
                        print(current_score, covar.id, covar.name, map_cell_score[gridid]['score_training'])

                if map_target_first != None and gridid in map_target_first.keys():
                    map_cell_score[gridid]['score_first'] += current_score_first                    

    df_cells = pd.DataFrame(map_cell_score.values())

    if demographic_group != None:
        demographic_group_dict = get_demographic(mesh, demographic_group)
        N = 0
        for gridid in demographic_group_dict.keys():
            N += demographic_group_dict[gridid]
    else:
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
                if demographic_group != None:
                    cummulated_length += df_cells.iloc[upper_first][demographic_group]
                else:    
                    cummulated_length += df_cells.iloc[upper_first].pobtot
                up_firstpper_first += 1
            aux_first = upper_first

            cases_percentil_first = df_cells.iloc[lower_first:upper_first].cases_first.sum()
            if demographic_group != None:
                pobtot_percentil_first = df_cells.iloc[lower_first:upper_first][demographic_group].sum()
            else:
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
            if demographic_group != None:
                cummulated_length += df_cells.iloc[upper_training][demographic_group]
            else:
                cummulated_length += df_cells.iloc[upper_training].pobtot

            upper_training += 1
        aux_training = upper_training

        cases_percentil_training = df_cells.iloc[lower_training:upper_training].cases_training.sum()

        if demographic_group != None:
            pobtot_percentil_training = df_cells.iloc[lower_training:upper_training][demographic_group].sum()
        else:
            pobtot_percentil_training = df_cells.iloc[lower_training:upper_training].pobtot.sum()

        p_training += [cases_percentil_training/pobtot_percentil_training for i in range(upper_training - lower_training)]
        percentil_training += [percentiles - d for i in range(upper_training - lower_training)]

    #print(len(p), len(percentil))
    df_cells['p_training'] = pd.Series(p_training)
    df_cells['percentil_training'] = pd.Series(percentil_training)

    if map_target_first != None:
        
        if False:
            '''
                Esta es la prediccion "aditiva"
            '''
            scores = np.array((df_cells['score_first']).tolist())
            probas = np.array((df_cells['p_first']).tolist())

            reg = LinearRegression()
            reg.fit(scores.reshape(-1, 1), probas)

            p_predicted_validation = reg.predict(np.array(df_cells['score_training']).reshape(-1, 1))
            df_cells['p_predicted_validation'] = df_cells['p_training'] + pd.Series(p_predicted_validation)

            df_cells['cases_predicted_validation'] = ((df_cells[demographic_group] if demographic_group != None else df_cells['pobtot']) - df_cells['cases_training'])*df_cells['p_predicted_validation']
        else:
            '''
                Esta es la prediccion "multiplicativa"
            '''
            if demographic_group == None:
                demographic_group = 'pobtot'
            df_cells['cases_predicted_validation'] = df_cells.apply(lambda row: 0 if row.cases_first == 0 else ((row.cases_training/row.cases_first)*row.p_training)*row[demographic_group], axis=1)
    return df_cells.to_dict(orient='records')


def get_target_filter(mesh, lim_inf, lim_sup, target, attribute_filter):
    '''
    '''
    attribute_map = query_map_builder(attribute_filter)
    target_filter = attribute_map
    
    target_filter = mesh_occurrence_condition(mesh, target_filter)

    if target == 'CONFIRMADO' or target == 'FALLECIDO':
        target_filter['variable_id__in'] = [5, 2, 3, 7]
    elif target == 'NEGATIVO':
        target_filter['variable_id__in'] = [1]
    elif target == 'PRUEBA':
        target_filter['variable_id__in'] = [1, 5, 2, 3]
    elif target == 'VACUNADO':
        target_filter['variable_id'] = 1

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


def get_covar_filter(mesh, lim_inf, lim_sup, covar):
    '''
    '''
    covar_filter = {}
    covar_filter = mesh_occurrence_condition(mesh, covar_filter)
    
    if covar == 'CONFIRMADO' or covar == 'FALLECIDO':
        covar_filter['variable_id__in'] = [5, 2, 3, 7]
    elif covar == 'NEGATIVO':
        covar_filter['variable_id__in'] = [1]
    elif covar == 'PRUEBA':
        covar_filter['variable_id__in'] = [1, 5, 2, 3]
    elif covar == 'VACUNADO':
        covar_filter['variable_id'] = 1
    
    if covar == 'FALLECIDO':
        if lim_inf != -99999:
            covar_filter['fecha_def__gte'] = lim_inf
        
        if lim_sup != -99999:
            covar_filter['fecha_def__lte'] = lim_sup
    else:
        if lim_inf != -99999:
            covar_filter['date_occurrence__gte'] = lim_inf
        
        if lim_sup != -99999:
            covar_filter['date_occurrence__lte'] = lim_sup
    
    return covar_filter


def calculate_epsilon_dge(target_filter={'variable_id__in': [2, 3], 'date_occurrence__lte': '2020-03-31',
    'date_occurrence__gte': '2020-03-01'}, mesh='mun', target='CONFIRMADO', demographic_group=None, 
    covariable_modifier=None):
    """
        Description: 
    """
    covar_cells_relation = {} 
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
                    'score':[],
                    }
    
    demographic_group_dict = {}
    if demographic_group != None:
        target_filter_short = {}
        target_filter_short['variable_id__in'] = target_filter['variable_id__in']
        if 'date_occurrence__lte' in target_filter_short.keys():
            target_filter_short['date_occurrence__lte'] = target_filter['date_occurrence__lte']
            target_filter_short['date_occurrence__gte'] = target_filter['date_occurrence__gte']
        else:
            target_filter_short['fecha_def__lte'] = target_filter['fecha_def__lte']
            target_filter_short['fecha_def__gte'] = target_filter['fecha_def__gte']
        demographic_group_dict = get_demographic_dge(mesh, demographic_group, target_filter_short)
        N = 0
        for gridid in demographic_group_dict.keys():
            N += demographic_group_dict[gridid]

    cells = get_mesh(mesh)
    map_cells_pobtot = {}
    for cell in cells:
        gridid = getattr(cell, 'gridid_' + mesh)
        if gridid in demographic_group_dict.keys():
            map_cells_pobtot[gridid] = demographic_group_dict[gridid]
        else:
            map_cells_pobtot[gridid] = 0
    #print(map_cells_pobtot)
    target_filter = mesh_occurrence_condition(mesh, target_filter)

    target_by_cell = OccurrenceCOVID19.objects.using('covid19').\
            values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    map_cell_target = {}
    for tc in target_by_cell:
        map_cell_target[tc['gridid_' + mesh]] = tc['tcount']
    
    Nc = 0
    for k in map_cell_target.keys():
        Nc += map_cell_target[k]
    PC = Nc/N
    Nc_ = N - Nc
    P_C = (N-Nc)/N
    s0 = np.log(PC/P_C)
    alpha = 0.01

    covars = [] 
    #comorbilities = ['neumonia']
    comorbilities = ['diabetes', 'neumonia', 'epoc', 'embarazo', 'asma', 'inmusupr', 
        'hipertension', 'cardiovascular', 'obesidad', 'renal_cronica','tabaquismo']
    for comorbility in comorbilities:
        if 'date_occurrence__gte' in target_filter.keys():
            lim_inf = target_filter['date_occurrence__gte']
            lim_sup = target_filter['date_occurrence__lte']
        else:
            lim_inf = target_filter['fecha_def__gte']
            lim_sup = target_filter['fecha_def__gte']
        results = build_covariable_attribute('covid19', mesh, comorbility, ['SI'], lim_inf, lim_sup)
    covars += results

    for covar in covars:
        dict_results['node'].append('covid19')
        dict_results['id'].append(covar['name'])
        dict_results['variable'].append(covar['name'] + ' ' + covar['interval'])            
        Nx = 0
        Ncx = 0
        cells_presence = covar['cells_' + mesh]
        for gridid in cells_presence:
            Nx += map_cells_pobtot[gridid] if gridid in map_cells_pobtot.keys() else 0
            if gridid in map_cell_target.keys():
                Ncx += map_cell_target[gridid] if gridid in map_cell_target.keys() else 0
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
        if Nx == 0 or PC == 0:
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

    return (dict_results, covars)


def calculate_score_dge(mesh='mun', target='CONFIRMADO', lim_inf_training='2020-03-01', lim_sup_training='2020-03-31', 
                    lim_inf_first=None, lim_sup_first=None, lim_inf_validation=None, lim_sup_validation=None, demographic_group=None, attribute_filter=None,
                    covariable_modifier=None):
    """
        Description: 
    """
    target_filter = get_target_filter(mesh, lim_inf_training, lim_sup_training, target, attribute_filter)

    target_filter_short = {}
    target_filter_short['variable_id__in'] = target_filter['variable_id__in']
    if 'date_occurrence__lte' in target_filter_short.keys():
        target_filter_short['date_occurrence__lte'] = target_filter['date_occurrence__lte']
        target_filter_short['date_occurrence__gte'] = target_filter['date_occurrence__gte']
    else:
        target_filter_short['fecha_def__lte'] = target_filter['fecha_def__lte']
        target_filter_short['fecha_def__gte'] = target_filter['fecha_def__gte']

    demographic_group_dict = {}
    if demographic_group != None:
        demographic_group_dict = get_demographic_dge(mesh, demographic_group, target_filter_short)

    cells = get_mesh(mesh)
    map_cells_pobtot = {}
    for cell in cells:
        gridid = getattr(cell, 'gridid_' + mesh)
        if gridid in demographic_group_dict.keys():
            map_cells_pobtot[gridid] = demographic_group_dict[gridid]
        else:
            map_cells_pobtot[gridid] = 0

    if lim_inf_first != None and lim_sup_first != None:
        target_filter_first = get_target_filter(mesh, lim_inf_first, lim_sup_first, target, attribute_filter)
        print(target_filter_first)
        target_first = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter_first).annotate(tcount=Count('id'))
        map_target_first = make_map(target_first, 'gridid_' + mesh, 'tcount')
        epsilon, covars_inf = calculate_epsilon_dge(target_filter_first, mesh, target, demographic_group, covariable_modifier)
        s0_first = epsilon['s0'][0]
        df_epsilon_first = pd.DataFrame(epsilon)
    else:
        map_target_first = None
        s0_first = 0

    if lim_inf_validation != None and lim_sup_validation != None:
        target_filter_validation = get_target_filter(mesh, lim_inf_validation, lim_sup_validation, target, attribute_filter)
        target_validation = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter_validation).annotate(tcount=Count('id'))
        map_target_validation = make_map(target_validation, 'gridid_' + mesh, 'tcount')
    else:
        map_target_validation = None

    map_cell_score = {}
    epsilon, covars = calculate_epsilon_dge(target_filter, mesh, target, demographic_group, covariable_modifier)
    s0 = epsilon['s0'][0]
    df_epsilon = pd.DataFrame(epsilon)
    percentiles = 20
    target_training = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    map_target_training = make_map(target_training, 'gridid_' + mesh, 'tcount')

    for cell in cells:
        gridid = getattr(cell, 'gridid_'  + mesh)
        map_cell_score[gridid] = {'score_training': s0, 'gridid': gridid, 'pobtot': cell.pobtot}
        map_cell_score[gridid]['cell'] = get_serialized_cell(cell, mesh)

        if demographic_group != None:
            map_cell_score[gridid][demographic_group] = map_cells_pobtot[gridid]

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

    for covar in covars:

        cells_presence = covar['cells_' + mesh]
        
        if df_epsilon[df_epsilon['id'] == covar['name']].shape[0] > 0:
            current_score = df_epsilon[df_epsilon['id'] == covar['name']].iloc[0].score
        else:
            continue
        
        df_aux = df_epsilon_first[df_epsilon_first['id'] == covar['name']]
        if map_target_first != None and df_aux.shape[0] > 0:
            current_score_first = df_aux.iloc[0].score
        else:
            current_score_first = 0       

        for gridid in cells_presence:
            
            if gridid in map_cell_score.keys():
                map_cell_score[gridid]['score_training'] += current_score

            if map_target_first != None and gridid in map_target_first.keys():
                map_cell_score[gridid]['score_first'] += current_score_first                    

    df_cells = pd.DataFrame(map_cell_score.values())

    N = 0
    if demographic_group != None:
        for gridid in map_cells_pobtot.keys():
            N += map_cells_pobtot[gridid]

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
                if demographic_group != None:
                    cummulated_length += df_cells.iloc[upper_first][demographic_group]
                upper_first += 1

            while cummulated_length >= N and upper_first < df_cells.shape[0]: 
                upper_first += 1
                print('-->', lower_first, upper_first)
            aux_first = upper_first

            print(d, lower_first, aux_first)
            cases_percentil_first = df_cells.iloc[lower_first:upper_first].cases_first.sum()
            if demographic_group != None:
                pobtot_percentil_first = df_cells.iloc[lower_first:upper_first][demographic_group].sum()

            p_first += [0 if pobtot_percentil_first == 0 else cases_percentil_first/pobtot_percentil_first for i in range(upper_first - lower_first)]
            percentil_first += [percentiles - d for i in range(upper_first - lower_first)]

        df_cells['p_first'] = pd.Series(p_first)
        df_cells['percentil_first'] = pd.Series(percentil_first)

    print(len(p_first))
    print(len(percentil_first))
    print(df_cells.shape)

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
            if demographic_group != None:
                cummulated_length += df_cells.iloc[upper_training][demographic_group]
            else:
                cummulated_length += df_cells.iloc[upper_training].pobtot

            upper_training += 1
        aux_training = upper_training

        cases_percentil_training = df_cells.iloc[lower_training:upper_training].cases_training.sum()

        if demographic_group != None:
            pobtot_percentil_training = df_cells.iloc[lower_training:upper_training][demographic_group].sum()
        else:
            pobtot_percentil_training = df_cells.iloc[lower_training:upper_training].pobtot.sum()

        p_training += [cases_percentil_training/pobtot_percentil_training for i in range(upper_training - lower_training)]
        percentil_training += [percentiles - d for i in range(upper_training - lower_training)]

    #print(len(p), len(percentil))
    df_cells['p_training'] = pd.Series(p_training)
    df_cells['percentil_training'] = pd.Series(percentil_training)

    if map_target_first != None:
        
        if False:
            '''
                Esta es la prediccion "aditiva"
            '''
            scores = np.array((df_cells['score_first']).tolist())
            probas = np.array((df_cells['p_first']).tolist())

            reg = LinearRegression()
            reg.fit(scores.reshape(-1, 1), probas)

            p_predicted_validation = reg.predict(np.array(df_cells['score_training']).reshape(-1, 1))
            df_cells['p_predicted_validation'] = df_cells['p_training'] + pd.Series(p_predicted_validation)

            df_cells['cases_predicted_validation'] = ((df_cells[demographic_group] if demographic_group != None else df_cells['pobtot']) - df_cells['cases_training'])*df_cells['p_predicted_validation']
        else:
            '''
                Esta es la prediccion "multiplicativa"
            '''
            if demographic_group == None:
                demographic_group = 'pobtot'
            df_cells['cases_predicted_validation'] = df_cells.apply(lambda row: 0 if row.cases_first == 0 else ((row.cases_training/row.cases_first)*row.p_training)*row[demographic_group], axis=1)

    df_cells = df_cells.fillna(0)
    return df_cells.to_dict(orient='records')