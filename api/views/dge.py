from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sklearn.metrics import roc_curve, auc
from ..utils.dge import *
from ..utils.aggregation import *
from ..models.occurrence import *
import pandas as pd
import datetime as dt

import json
import os
import time


class Covariables(APIView):

    def post(self, request):
        target = None
        initial_date = None
        period = None
        covariables = None
        include_inegi_vars = False
        filter_inegi = []

        try:
            if 'target' in request.data.keys():
                target = request.data['target']
            else:
                return Response({"message": "`target` parameter not found"},\
                    status=status.HTTP_400_BAD_REQUEST)

            if 'initial_date' in request.data.keys():
                initial_date = request.data['initial_date']
            else:
                return Response({"message": "`initial_date` parameter not found"},\
                    status=status.HTTP_400_BAD_REQUEST)

            if 'period' in request.data.keys():
                period = request.data['period']
            else:
                return Response({"message": "`period` parameter not found"},\
                    status=status.HTTP_400_BAD_REQUEST)

            if 'covariables' in request.data.keys():
                covariables = request.data['covariables']
            else:
                covariables = None

            try:
                include_inegi_vars = request.data['include_inegi_vars']
                try:
                    filter_inegi = request.data['filter_inegi']
                except:
                    filter_inegi = []
            except:
                include_inegi_vars = False

            reports = os.listdir('./reports/')
            report_cov = 'dge-covariables-' + target + '-' + initial_date + '-' + str(period) + '.csv'
            
            if report_cov in reports:    
                df = pd.read_csv('./reports/{0}'.format(report_cov))
                if covariables != None:
                    df = df[df['variable'].isin(covariables)]
                results_covariables = df.to_dict(orient='records')
                if include_inegi_vars:
                    df_inegi = pd.read_csv('./reports/inegi_covariables-' + target + '-' + str(initial_date) + '.csv', dtype={'gridid_mun': str})
                    df_inegi = df_inegi[df_inegi['variable'].isin(filter_inegi)]
                    for index, row in df_inegi.iterrows():
                        results_covariables.append({
                            'variable': row['variable'],
                            'value': row['value'],
                            'Nx': row['Nx'], 
                            'Ncx': row['Ncx'], 
                            'PCX': row['PCX'], 
                            'PC': row['PC'], 
                            'Nc': row['Nc'], 
                            'N': row['N'], 
                            'epsilon': row['epsilon'],
                            'Nc_': row['Nc'],
                            'Nc_x': row['Nc_x'],
                            'P_C': row['P_C'],
                            'P_CX': row['P_CX'],
                            's0': row['s0'],
                            'score': row['score']
                        })
                return Response({'covariables':  results_covariables}, status=status.HTTP_200_OK)

            target_attributes = {}
            delta_period = dt.timedelta(days = period)
            final_date = dt.datetime.strptime(initial_date, '%Y-%m-%d') + delta_period
            target_attributes['date_occurrence__gte'] = initial_date
            target_attributes['date_occurrence__lt'] = final_date.strftime('%Y-%m-%d')
            target_attributes['variable_id__in'] = [5, 2, 3, 7]
            
            occurrences = OccurrenceCOVID19.objects.using('covid19').\
                filter(**target_attributes).values()
            
            print(target_attributes)
            #print('# Occs: ' + str(occurrences.count()))

            results_covariables = calculate_results_covariables(target, occurrences)            
            return Response({'covariables': results_covariables}, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Cells(APIView):
    
    def post(self, request):
        target = None
        initial_date = None
        period = None

        
        if 'target' in request.data.keys():
            target = request.data['target']
        else:
            return Response({"message": "`target` parameter not found"},\
                status=status.HTTP_400_BAD_REQUEST)

        if 'initial_date' in request.data.keys():
            initial_date = request.data['initial_date']
        else:
            return Response({"message": "`initial_date` parameter not found"},\
                status=status.HTTP_400_BAD_REQUEST)

        if 'period' in request.data.keys():
            period = request.data['period']
        else:
            return Response({"message": "`period` parameter not found"},\
                status=status.HTTP_400_BAD_REQUEST)

        target_attributes = {}
        delta_period = dt.timedelta(days = period)
        final_date = dt.datetime.strptime(initial_date, '%Y-%m-%d') + delta_period
        target_attributes['date_occurrence__gte'] = initial_date
        target_attributes['date_occurrence__lt'] = final_date.strftime('%Y-%m-%d')
        target_attributes['variable_id__in'] = [5, 2, 3, 7]
        
        occurrences = OccurrenceCOVID19.objects.using('covid19').\
            filter(**target_attributes).values()

        results_cells = calculate_results_cells(target, occurrences)
        return Response({'occurences': results_cells}, status=status.HTTP_200_OK)


class GetHistoricalProfile(APIView):

    def post(self, request):
        covariables = [\
            'gridid_mun', \
            'sexo', 'embarazo', 'diabetes', \
            'epoc', 'asma', 'inmusupr', \
            'hipertension', 'cardiovascular', \
            'obesidad', 'renal_cronica', \
            'tabaquismo']
        target_column_map = {\
            'HOSPITALIZADO': 'hospitalizado', \
            'NEUMONIA': 'neumonia', \
            'INTUBADO': 'intubado',
            'UCI': 'uci'}
        try:
            data = request.data

            if data['target'] == 'UCI':
                covariables.append('hospitalizado')
            if data['target'] == 'NEUMONIA':
                covariables.append('hospitalizado')
                covariables.append('uci')
            elif data['target'] == 'INTUBADO':
                covariables.append('hospitalizado')
                covariables.append('uci')
                covariables.append('neumonia')
            elif data['target'] == 'FALLECIDO':
                covariables.append('hospitalizado')
                covariables.append('uci')
                covariables.append('neumonia')
                covariables.append('intubado')

            initial_date = None
            if 'initial_date' in data.keys() and data['initial_date'] != None:
                initial_date = data['initial_date']
            else:
                return Response({"message": "`initial_date` parameter not found"},\
                    status=status.HTTP_400_BAD_REQUEST)

            reports = os.listdir('./reports/')
            reports_cov = [r for r in reports if r.startswith('dge-') and data['target'] in r and 'covariables' in r and r <= 'dge-covariables-' + data['target'] + '-' + initial_date + '.csv']
            reports_cov.sort()
            reports_cov = reports_cov[-5:] 
            reports_occ = [r for r in reports if r.startswith('dge-') and data['target'] in r and 'occurrences' in r and r <= 'dge-occurrences-' + data['target'] + '-' + initial_date + '.csv']
            reports_occ.sort()
            reports_occ = reports_occ[-5:]
            reports = None
            periods = {}
            for rcov in reports_cov:
                df = pd.read_csv('./reports/{0}'.format(rcov))
                score_total = df.iloc[0]['s0']
                #print(df)
                date = rcov.split(data['target']+'-')[1].split('.csv')[0][:-3]
                periods[date] = {}
                age_group = map_age_group(data['edad'])
                score = df[(df['variable'] == 'edad') & (df['value'] == age_group)].iloc[0]['score']
                epsilon = df[(df['variable'] == 'edad') & (df['value'] == age_group)].iloc[0]['epsilon']
                pcx = df[(df['variable'] == 'edad') & (df['value'] == age_group)].iloc[0]['PCX']
                score_total += score
                periods[date]['edad'] = {'value': age_group, 'score': score, 'epsilon': epsilon, 'PCX': pcx}

                for covariable in covariables:
                    #print(covariable)
                    try:
                        
                        if covariable == 'hospitalizado' and data[covariable] == 'SI':
                            data[covariable] = 'HOSPITALIZADO'
                        elif covariable == 'hospitalizado' and data[covariable] == 'NO':
                            data[covariable] = 'AMBULATORIO'
                        if covariable == 'intubado' and data[covariable] == 'NO':
                            data[covariable] = 'NO APLICA'

                        score = df[(df['variable'] == covariable) & (df['value'] == data[covariable])].iloc[0]['score']
                        epsilon = df[(df['variable'] == covariable) & (df['value'] == data[covariable])].iloc[0]['epsilon']
                        pcx = df[(df['variable'] == covariable) & (df['value'] == data[covariable])].iloc[0]['PCX']
                        score_total += score
                        periods[date][covariable] = {'value': data[covariable], 'score': score, 'epsilon': epsilon, 'PCX': pcx}
                        
                        if covariable == 'hospitalizado':
                            periods[date][covariable]['value'] = 'SI' if periods[date][covariable]['value'] == 'HOSPITALIZADO' else 'NO'
                        if covariable == 'intubado' and data[covariable] == 'NO APLICA':
                            periods[date][covariable]['value'] = 'NO'

                    except Exception as e:
                        print('error cov ', covariable, str(e))
                
                periods[date]['profile_score'] = score_total

            df = None
            for rocc in reports_occ:
                date = rocc.split(data['target']+'-')[1].split('.csv')[0][:-3]
                df = pd.read_csv('./reports/{0}'.format(rocc))
                df = df.sort_values('score', ascending=False)
                df = df.reset_index(drop=True)
                percentile_length = df.shape[0]/20
                for i in range(20):
                    lim_inf = int(percentile_length*i)
                    lim_sup = int(percentile_length*(i+1)-1)
                    max_score = df.iloc[lim_inf]['score']
                    min_score = df.iloc[lim_sup]['score']
                    periods[date]['bin-{0}'.format(20-i)] = {}
                    periods[date]['bin-{0}'.format(20-i)]['max_score'] = max_score
                    periods[date]['bin-{0}'.format(20-i)]['min_score'] = min_score

                    Nc = 0
                    df_train = df.iloc[lim_inf:lim_sup+1]
                    #print(df_train['fecha_def'].unique())
                    if data['target'] == 'FALLECIDO':
                        Nc = df_train[df_train['fecha_def']!='9999-99-99'].shape[0]
                    elif data['target'] != 'HOSPITALIZADO':
                        target_column = target_column_map[data['target']]
                        Nc = df_train[df_train[target_column]=='SI' if target_column != 'hospitalizado' else 'HOSPITALIZADO'].shape[0]
                    
                    probability = Nc/float(percentile_length)
                    periods[date]['bin-{0}'.format(20-i)]['probability'] = probability

                    periods[date]['profile_bin'] = 20
                    if periods[date]['profile_score'] <= max_score:
                        periods[date]['profile_bin'] = 20 - i
                        periods[date]['target_profile_probability'] = probability

            return Response({'data': periods}, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class AvailableDateAnalysis(APIView):

    def get(self, request):
        try:
            target = None
            targets = None
            available_dates = []
            if not 'target' in request.GET.keys() and not 'targets' in request.GET.keys():
                return Response({'message': '`target` parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if not 'targets' in request.GET.keys():
                    target = request.GET['target']
                else:
                    targets = request.GET['targets']
                    targets = targets.split(',')
            reports = os.listdir('./reports/')
            if target != None:
                reports_cov = [r for r in reports if r.startswith('dge-') and target in r and 'occurrences' in r]
                available_dates = [rcov.split(target+'-')[1].split('.csv')[0][:-3] for rcov in reports_cov]
            else:
                for target in targets:
                    reports_cov = [r for r in reports if r.startswith('dge-') and target in r and 'occurrences' in r]
                    ad_aux = [rcov.split(target+'-')[1].split('.csv')[0][:-3] for rcov in reports_cov]
                    #print(target, available_dates, ad_aux)
                    if len(available_dates) == 0:
                        available_dates = ad_aux
                    else:
                        available_dates = [r for r in ad_aux if r in available_dates] 
                    available_dates = list(set(available_dates))
            return Response({
                'data': available_dates}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetProfileCovariable(APIView):

    def post(self, request):
        try:
            target = request.data['target']
            date = request.data['date']
            reports = os.listdir('./reports/')
            report_cov = None
            for r in reports:
                if target in r and date in r and 'occurrences' in r:
                    report_cov = './reports/dge-covariables-' + target + '-' + date + '-30' + '.csv'
                    break
            if report_cov == None:
                return Response({'message': '`date` not available'}, status=status.HTTP_400_BAD_REQUEST)
            df_cov = pd.read_csv(report_cov)
            return Response({'data': df_cov.to_dict(orient='records')}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetROCCurve(APIView):

    def post(self, request):
        try:
            target = request.data['target']
            date = request.data['date']
            reports = os.listdir('./reports/')
            report_occ = None
            for r in reports:
                if target in r and date in r and 'occurrences' in r:
                    report_occ = './reports/' + r
                    break
            if report_occ == None:
                return Response({'message': '`date` not available'}, status=status.HTTP_400_BAD_REQUEST)
           
            df_occ = pd.read_csv(report_occ)
            if target != 'CONFIRMADO' and target != 'FALLECIDO':
                target_column_map = {\
                    'HOSPITALIZADO': 'tipo_paciente', \
                    'NEUMONIA': 'neumonia', \
                    'INTUBADO': 'intubado',
                    'UCI': 'uci'}
                if target == 'HOSPITALIZADO':
                    df_occ = df_occ[(df_occ[target_column_map[target]]=='HOSPITALIZADO') | (df_occ[target_column_map[target]]=='AMBULATORIO')]
                else:
                    df_occ = df_occ[(df_occ[target_column_map[target]]=='SI') | (df_occ[target_column_map[target]]=='NO')]
            df_occ = df_occ.sort_values('score', ascending=True)
            df_occ['target'] = df_occ.apply(lambda x: is_target(x, target), axis=1)
            df_occ = df_occ[['score', 'target']]
            
            scores_l = []
            targets_l = []
            for index, row in df_occ.iterrows():
                #print(index, row)
                scores_l.append(row['score'])
                targets_l.append(row['target'])
            fpr, tpr, thresholds = roc_curve(targets_l, scores_l, pos_label=1)
            roc_auc = auc(fpr, tpr)
            fpr_list = fpr.tolist()
            tpr_list = tpr.tolist()

            #return Response({'data': df_occ.to_dict(orient='records')}, status=status.HTTP_200_OK)
            return Response({"data_roc":[{"fpr":fpr_list}, {"tpr":tpr_list}, {"auc":roc_auc}]}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DGEFreeMode(APIView):

    def post(self, request):
        try:
            starting_time = time.time()
            target = request.data['target']
            date = request.data['date']
            covars = request.data['covariables']
            include_inegi_vars = False

            try:
                include_inegi_vars = request.data['include_inegi_vars']
            except:
                include_inegi_vars = False

            reports = os.listdir('./reports/')
            report_cov = None
            for r in reports:
                if target in r and date in r and 'occurrences' in r:
                    report_cov = './reports/dge-covariables-' + target + '-' + date + '-30' + '.csv'
                    break
            if report_cov == None:
                return Response({'message': '`date` not available'}, status=status.HTTP_400_BAD_REQUEST)

            target_attributes = {}
            delta_period = dt.timedelta(days = 30)
            final_date = dt.datetime.strptime(date, '%Y-%m-%d') + delta_period
            target_attributes['date_occurrence__gte'] = date
            target_attributes['date_occurrence__lt'] = final_date.strftime('%Y-%m-%d')
            target_attributes['variable_id__in'] = [5, 2, 3, 7]
            
            #occurrences = OccurrenceCOVID19.objects.using('covid19').\
            #    filter(**target_attributes).values()
            occurrences = pd.read_csv('./reports/occurrences_' + date + '.csv')
            occurrences = occurrences.sample(frac=1).reset_index(drop=True)
            occurrences = occurrences.iloc[:5000]
            occurrences = occurrences.rename(columns={'covariable_id': 'variable_id'})
            occurrences = occurrences.to_dict(orient='records')

            print('NUMBER OCCS ', len(occurrences))
            print(occurrences[0])

            df_cov = pd.read_csv(report_cov)
            #print(df_cov)

            df_cov = df_cov[df_cov['variable'].isin(covars)]

            checkpoint = time.time()
            print('BEFORE CALCULATE SCORES', checkpoint -starting_time, 'secs')
            starting_time = checkpoint

            occs = calculate_results_cells_free_mode(df_cov, covars, target, occurrences, include_inegi_vars, date)
            checkpoint = time.time()
            print('AFTER CALCULATE SCORES', checkpoint -starting_time, 'secs')
            starting_time = checkpoint
            df_occ = pd.DataFrame(occs)
            checkpoint = time.time()
            print('AFTER CREATE DF ', checkpoint -starting_time, 'secs')
            starting_time = checkpoint
            df_occ = df_occ.sort_values(by='score', ascending=False)
            df_occ['target'] = df_occ.apply(lambda x: is_target(x, target), axis=1)

            #print(df_occ)

            score_decil_bar = []
            N = df_occ.shape[0]
            N_target = df_occ['target'].sum()
            recall = 0
            for i in range(10):
                #print(i*int(N/10), (i+1)*int(N/10))
                #print(df_occ[i*int(N/10): (i+1)*int(N/10)])
                recall += df_occ.iloc[i*int(N/10): (i+1)*int(N/10)]['target'].sum()
                score_decil_bar.append({
                    'bin': 10 - i,
                    'sum': df_occ.iloc[i*int(N/10): (i+1)*int(N/10)]['score'].sum(),
                    'mean': df_occ.iloc[i*int(N/10): (i+1)*int(N/10)]['score'].mean(),
                    'recall': recall/N_target
                    })

            return Response({'score_decil_bar': score_decil_bar}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DGENets(APIView):

    def post(self, request):
        try:
            starting_time = time.time()
            targets = request.data['targets']
            date = request.data['date']
            covars = request.data['covariables']
            filter_inegi = []
            try:
                include_inegi_vars = request.data['include_inegi_vars']
                try:
                    filter_inegi = request.data['filter_inegi']
                except:
                    filter_inegi = []
            except:
                include_inegi_vars = False

            reports = os.listdir('./reports/')
            report_cov = None
            is_available = False

            for target in targets:
                report_cov = 'dge-covariables-' + target + '-' + date + '-30' + '.csv'
                #print(report_cov, reports)
                if report_cov in reports:
                    is_available = True
                if not is_available:
                    return Response({'message': '`date` not available'}, status=status.HTTP_400_BAD_REQUEST)

            if include_inegi_vars:
                df_inegi_cov = pd.read_csv('./reports/inegi_covariables-' + target + '-' + str(date) + '.csv', dtype={'gridid_mun': str})
                df_inegi_cov = df_inegi_cov[df_inegi_cov['variable'].isin(filter_inegi)]
                df_inegi_cov = df_inegi_cov[['id', 'variable', 'value', 'Nx', 'Ncx', \
                    'PCX', 'PC', 'Nc', 'N', 'epsilon', 'Nc_', 'Nc_x', 'P_C', 'P_CX', \
                    's0', 'score']]
                df_inegi_occ = OccurrenceINEGI2020.objects.using('inegi2020')\
                    .filter(variable_id__in=df_inegi_cov['id'].unique().tolist())\
                    .values('gridid_mun', 'variable_id')
                df_inegi_occ = pd.DataFrame(df_inegi_occ)
            nodes = []
            edges = []
            added_nodes = {}
            checkpoint = time.time()
            print('BEFORE START ', checkpoint -starting_time, 'secs')
            starting_time = checkpoint
            for target in targets:
                target_attributes = {}
                delta_period = dt.timedelta(days = 30)
                final_date = dt.datetime.strptime(date, '%Y-%m-%d') + delta_period
                if target == 'FALLECIDO':
                    target_attributes['fecha_def__gte'] = date
                    target_attributes['fecha_def__lt'] = final_date.strftime('%Y-%m-%d')
                else:
                    target_attributes['date_occurrence__gte'] = date
                    target_attributes['date_occurrence__lt'] = final_date.strftime('%Y-%m-%d')
                target_attributes['variable_id__in'] = [5, 2, 3, 7]
                is_target_query(target_attributes, target)
                #print(target_attributes)

                checkpoint = time.time()
                print('PROCESSING ', target, ' occurrences query ', checkpoint -starting_time, 'secs')
                occurrences = OccurrenceCOVID19.objects.using('covid19').\
                    filter(**target_attributes).values('gridid_mun',
                                'edad', 'sexo', 'neumonia', 'embarazo',
                               'diabetes', 'epoc', 'asma', 'inmusupr', 'hipertension',
                               'cardiovascular', 'obesidad', 'renal_cronica', 'tabaquismo', 'uci',
                               'intubado', 'tipo_paciente').distinct()
                starting_time = checkpoint
                #print(occurrences.count())

                checkpoint = time.time()
                print('PROCESSING ', target, ' reading covariable file ', checkpoint -starting_time, 'secs')
                report_cov = './reports/dge-covariables-' + target + '-' + date + '-30' + '.csv'
                df_cov = pd.read_csv(report_cov)
                df_cov = df_cov[df_cov['variable'].isin(covars)]
                starting_time = checkpoint

                checkpoint = time.time()
                print('PROCESSING ', target, ' calculating score ', checkpoint -starting_time, 'secs')
                df_occ = pd.DataFrame(occurrences)
                df_occ['edad'] = df_occ['edad'].apply(lambda x: map_age_group(x))
                print(df_occ)
                starting_time = checkpoint

                target_id = get_random_string(5)
                nodes.append({'id': target_id, 'type': 'target', \
                        'name': target, 'occs': df_occ.shape[0]})
                added_nodes[target] = target_id

                checkpoint = time.time()
                print('PROCESSING ', target, ' calculate net ', checkpoint -starting_time, 'secs')
                for index, row in df_cov.iterrows():
                    df = df_occ[df_occ[row['variable']] == row['value']]
                    if not row['variable'] + ':' + row['value'] in added_nodes.keys():
                        variable_id = get_random_string(5)
                        nodes.append({'id': variable_id, 'type': 'variable', \
                                        'name': row['variable'] + ':' + row['value'], \
                                        'occs': df.shape[0]})
                        added_nodes[row['variable'] + ':' + row['value']] = variable_id
                    else:
                        variable_id = added_nodes[row['variable'] + ':' + row['value']]
                    edges.append({'target': target_id, 'variable': variable_id, \
                                'epsilon': row['epsilon'], 'score': row['score'], \
                                'occs': df_occ[df_occ[row['variable']] == row['value']].shape[0]})

                if include_inegi_vars:
                    target_cells = df_occ['gridid_mun'].unique()
                    covariable_ids = df_inegi_occ[df_inegi_occ['gridid_mun'].isin(target_cells)]['variable_id'].unique()
                    df_inegi_cov = df_inegi_cov[df_inegi_cov['id'].isin(covariable_ids)]
                    for index, row in df_inegi_cov.iterrows():
                        if not row['variable'] in added_nodes.keys():
                            variable_id = get_random_string(5)
                            nodes.append({'id': variable_id, 'type': 'variable', \
                                        'name': row['variable'] + ':' + row['value'], \
                                        'occs': df_inegi_occ[df_inegi_occ['variable_id'] == row['id']].shape[0]})
                            added_nodes[row['variable'] + ':' + row['value']] = variable_id
                        else:
                            variable_id = added_nodes[row['variable'] + ':' + row['value']]
                        edges.append({'target': target_id, 'variable': variable_id, \
                                'epsilon': row['epsilon'], 'score': row['score'], \
                                'occs': df_inegi_occ[(df_inegi_occ['variable_id'] == row['id']) & (df_inegi_occ['gridid_mun'].isin(target_cells))].shape[0]})
                starting_time = checkpoint
            return Response({'nodes': nodes, 'edges': edges}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)