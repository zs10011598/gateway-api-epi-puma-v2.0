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


class Covariables(APIView):

    def post(self, request):
        target = None
        initial_date = None
        period = None

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
            if not 'target' in request.GET.keys():
                return Response({'message': '`target` parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                target = request.GET['target']
            reports = os.listdir('./reports/')
            reports_cov = [r for r in reports if r.startswith('dge-') and target in r and 'occurrences' in r]
            return Response({
                'data': [rcov.split(target+'-')[1].split('.csv')[0][:-3] for rcov in reports_cov]}, status=status.HTTP_200_OK)
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
            target = request.data['target']
            date = request.data['date']
            covars = request.data['covariables'] 
            
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
            
            occurrences = OccurrenceCOVID19.objects.using('covid19').\
                filter(**target_attributes).values()

            df_cov = pd.read_csv(report_cov)
            #print(df_cov)

            df_cov = df_cov[df_cov['variable'].isin(covars)]

            occs = calculate_results_cells_free_mode(df_cov, covars, target, occurrences)

            return Response({'data': occs}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)