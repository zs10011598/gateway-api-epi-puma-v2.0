from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sklearn.metrics import roc_curve
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
            
            print('# Occs: ' + str(occurrences.count()))

            results_covariables = calculate_results_covariables(target, occurrences)
            return Response({'covariables': results_covariables}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Cells(APIView):
    
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

            results_cells = calculate_results_cells(target, occurrences)
            return Response({'occurences': results_cells}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            'HOSPITALIZADO': 'uci', \
            'NEUMONIA': 'neumonia', \
            'INTUBADO': 'intubado'}
        try:
            data = request.data
            reports = os.listdir('./reports/')
            reports_cov = [r for r in reports if r.startswith('dge-') and data['target'] in r and 'covariables' in r]
            reports_cov.sort()
            reports_cov = reports_cov[-5:] 
            reports_occ = [r for r in reports if r.startswith('dge-') and data['target'] in r and 'occurrences' in r]
            reports_occ.sort()
            reports_occ = reports_occ[-5:]
            reports = None
            periods = {}
            for rcov in reports_cov:
                score_total = 0
                df = pd.read_csv('./reports/{0}'.format(rcov))
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
                    try:
                        score = df[(df['variable'] == covariable) & (df['value'] == data[covariable])].iloc[0]['score']
                        epsilon = df[(df['variable'] == covariable) & (df['value'] == data[covariable])].iloc[0]['epsilon']
                        pcx = df[(df['variable'] == covariable) & (df['value'] == data[covariable])].iloc[0]['PCX']
                        score_total += score
                        periods[date][covariable] = {'value': data[covariable], 'score': score, 'epsilon': epsilon, 'PCX': pcx}                    
                    except Exception as e:
                        print(str(e))
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
                    df_train = df[lim_inf:lim_sup+1]
                    if data['target'] == 'CONFIRMADO' or data['target'] == 'FALLECIDO':
                        Nc = df_train[df_train['variable_id'].isin([5, 2, 3, 7])].shape[0]
                    else:
                        target_column = target_column_map[data['target']]
                        Nc = df_train[(df_train['variable_id'].isin([5, 2, 3, 7])) & (df_train[target_column]=='SI')]\
                            .shape[0]
                    probability = Nc/float(percentile_length)
                    periods[date]['bin-{0}'.format(20-i)]['probability'] = probability

                    periods[date]['profile_bin'] = 20
                    if periods[date]['profile_score'] <= max_score:
                        periods[date]['profile_bin'] = 20 - i
                        periods[date]['target_profile_probability'] = probability

            return Response({'data': periods}, status=status.HTTP_200_OK)
        except Exception as e:
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
                    'HOSPITALIZADO': 'uci', \
                    'NEUMONIA': 'neumonia', \
                    'INTUBADO': 'intubado'}
                df_occ = df_occ[(df_occ[target_column_map[target]]=='SI') | (df_occ[target_column_map[target]]=='NO')]
            df_occ = df_occ.sort_values('score', ascending=True)
            df_occ['target'] = df_occ.apply(lambda x: is_target(x, target), axis=1)
            df_occ = df_occ[['score', 'target']]
            
            scores = []
            targets = []
            for row, index in df_occ.iterrows():
               scores.append(row['score'])
               target.append(row['target']) 
            
            fpr, tpr, thresholds = roc_curve(targets, scores, pos_label=1)
            fpr_list = fpr.tolist()
            tpr_list = tpr.tolist()

            #return Response({'data': df_occ.to_dict(orient='records')}, status=status.HTTP_200_OK)
            return Response({"data_roc":[{"fpr":fpr_list},{"tpr":tpr_list}]}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
