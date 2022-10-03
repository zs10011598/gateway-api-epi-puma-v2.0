from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
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

            if target == 'FALLECIDO':
                target_attributes['fecha_def__gte'] = initial_date
                target_attributes['fecha_def__lt'] = final_date.strftime('%Y-%m-%d')
            else:
                target_attributes['date_occurrence__gte'] = initial_date
                target_attributes['date_occurrence__lt'] = final_date.strftime('%Y-%m-%d')
            
            occurrences = OccurrenceCOVID19.objects.using('covid19').filter(**target_attributes).values()
            
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

            if target == 'FALLECIDO':
                target_attributes['fecha_def__gte'] = initial_date
                target_attributes['fecha_def__lt'] = final_date.strftime('%Y-%m-%d')
            else:
                target_attributes['date_occurrence__gte'] = initial_date
                target_attributes['date_occurrence__lt'] = final_date.strftime('%Y-%m-%d')
            
            occurrences = OccurrenceCOVID19.objects.using('covid19').filter(**target_attributes).values()

            results_cells = calculate_results_cells(target, occurrences)
            return Response({'occurences': results_cells}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetHistoricalProfile(APIView):

    def post(self, request):
        covariables = ['gridid_mun', 'sexo', 'embarazo', 'diabetes', 'epoc', 'asma', 'inmusupr', 'hipertension', 'cardiovascular', 'obesidad', 'renal_cronica', 'tabaquismo']
        target_column_map = {'HOSPITALIZADO': 'uci', 'NEUMONIA': 'neumonia', 'INTUBADO': 'intubado'}
        try:
            data = request.data
            reports = os.listdir('./reports/')                      
            reports_cov = [r for r in reports if r.startswith('dge-') and data['target'] in r and 'covariables' in r]
            reports_occ = [r for r in reports if r.startswith('dge-') and data['target'] in r and 'occurrences' in r]
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
                score_total += score
                periods[date]['edad'] = {'value': age_group, 'score': score}

                for covariable in covariables:
                    try:
                        score = df[(df['variable'] == covariable) & (df['value'] == data[covariable])].iloc[0]['score']
                        score_total += score
                        periods[date][covariable] = {'value': data[covariable], 'score': score}                    
                    except Exception as e:
                        print(str(e))
                periods[date]['profile_score'] = score_total

            df = None
            for rocc in reports_occ:
                date = rcov.split(data['target']+'-')[1].split('.csv')[0][:-3]
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

                    if periods[date]['profile_score'] >= min_score:
                        periods[date]['profile_bin'] = 20 - i
                        periods[date]['target_profile_probability'] = probability

            return Response({'data': periods}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)