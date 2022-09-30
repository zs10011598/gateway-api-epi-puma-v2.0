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
                target_attributes['fecha_def__lte'] = final_date.strftime('%Y-%m-%d')
            else:
                target_attributes['date_occurrence__gte'] = initial_date
                target_attributes['date_occurrence__lte'] = final_date.strftime('%Y-%m-%d')
            
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
                target_attributes['fecha_def__lte'] = final_date.strftime('%Y-%m-%d')
            else:
                target_attributes['date_occurrence__gte'] = initial_date
                target_attributes['date_occurrence__lte'] = final_date.strftime('%Y-%m-%d')
            
            occurrences = OccurrenceCOVID19.objects.using('covid19').filter(**target_attributes).values()

            results_cells = calculate_results_cells(target, occurrences)
            return Response({'occurences': results_cells}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'message': 'something was wrong: {0}'.format(str(e))}\
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
