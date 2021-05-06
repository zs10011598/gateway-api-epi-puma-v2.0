from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..utils.analysis_population import *



class Covariables(APIView):

	def post(self, request):
		"""
			
		"""
		computations  = calculate_epsilon(dbs=['inegi2020'], target_filter={'variable_id__in': [2, 3], 
                                                               'date_occurrence__lte': '2020-03-31',
                                                               'date_occurrence__gte': '2020-03-01'}, mesh='mun')
		N = len(computations['N'])
		response = []
		for i in range(N):
			response.append({
							 'node': computations['node'][i],
							 'id': computations['id'][i],
							 'variable': computations['variable'][i],
							 'Nx': computations['Nx'][i],
							 'Ncx': computations['Ncx'][i],
							 'PCX': computations['PCX'][i], 
		                     'PC': computations['PC'][i], 
		                     'Nc': computations['Nc'][i], 
		                     'N': computations['N'][i], 
		                     'epsilon': computations['epsilon'][i],
		                     'Nc_': computations['Nc_'][i],
		                     'Nc_x': computations['Nc_x'][i],
		                     'P_C': computations['P_C'][i],
		                     'P_CX': computations['P_CX'][i],
		                     's0': computations['s0'][i],
		                     'score': computations['score'][i]
				})
		return Response(response, status=status.HTTP_200_OK)


class Cells(APIView):

	def post(self, request):
		"""
			
		"""
		response = calculate_score(dbs=['inegi2020'], target_filter={ 'variable_id__in': [2, 3], 
                                                       'date_occurrence__lte': '2020-03-31',
                                                       'date_occurrence__gte': '2020-03-01'}, mesh='mun')
		return Response(response, status=status.HTTP_200_OK)