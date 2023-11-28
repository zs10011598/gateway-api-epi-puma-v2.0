from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..serializers.symptoms import SymptompsCovariablesRequest
from ..utils.dge import *

import pandas as pd


class Covariables(APIView):

    def post(self, request):

    	sympt_request = SymptompsCovariablesRequest(data=request.data)

    	if not sympt_request.is_valid():
    		return Response({'message': 'missing parameters'}, \
    			status=status.HTTP_400_BAD_REQUEST)

    	try:
    		print(sympt_request.data)
    		age_group = map_age_group(sympt_request.data['age'])
	    	symptoms = ['asma', 'atralgias', 'cefalea', 'cianosis', 'conjuntivitis', \
	    				'diabetes', 'diarrea', 'disnea', 'dolor_abdominal', 'dolor_toracico', \
	    				'embarazada', 'enfermedad_cardiaca', 'epoc', 'escalofrios', 'fiebre', \
	    				'hipertension', 'inmunosupresion', 'insubis', 'insuf_renal_cronica', \
	    				'irritabilidad', 'mialgias', 'obesidad', 'odinogia', 'otra_condicion', \
	    				'polipnea', 'rinorea', 'tos', 'vacunado', 'vih', 'vomito']
    		df = pd.read_csv('./reports/weights_covars-' + age_group + '-' + \
    			sympt_request.data['gender'] + '-only-symptoms-.csv')
    		results_covariables = []
    		for symptom in symptoms:
    			row = df[(df['variable'] == symptom) & (df['value'] == sympt_request.data[symptom])]
    			if row.shape[0] > 0:
    				row = row.iloc[0]
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
    		return Response({'data': results_covariables}, status=status.HTTP_200_OK)
    	except Exception as e:
    		return Response({'message': 'error: ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)