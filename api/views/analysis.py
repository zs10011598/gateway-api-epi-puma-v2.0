from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models.occurrence import *
import pandas as pd
from .analysis_population import get_target_filter
from ..utils.analysis import *
import json


class Covariables(APIView):

	def post(self, request):
		"""
			
		"""
		if 'covariables' in request.data.keys():
			dbs = request.data['covariables']
		else:
			return Response({"message": "`covariables` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'mesh' in request.data.keys():
			mesh = request.data['mesh']
		else:
			return Response({"message": "`mesh` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)
		
		if 'target' in request.data.keys():
			target = request.data['target']
		else:
			return Response({"message": "`target` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'lim_inf_training' in request.data.keys():
			lim_inf_training = request.data['lim_inf_training']
		else:
			lim_inf_training = -99999

		if 'lim_sup_training' in request.data.keys():
			lim_sup_training = request.data['lim_sup_training']
		else:
			lim_sup_training = -99999

		if 'attribute_filter' in request.data.keys():
			attribute_filter = request.data['attribute_filter']
		else:
			attribute_filter = {}

		if 'demographic_group' in request.data.keys():
			demographic_group = request.data['demographic_group']
		else:
			demographic_group = None

		target_filter = get_target_filter(mesh, lim_inf_training, lim_sup_training, target, attribute_filter)

		computations  = calculate_epsilon(dbs, target_filter, mesh, target, demographic_group)

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

		return Response({'data': response}, status=status.HTTP_200_OK)


class CellsEnsamble(APIView):

    def post(self, request):

        jsonf = None
        with open('./mock/epi-species-mock.json') as f:
            jsonf = str(f.read())

        return Response(json.loads(jsonf), status=status.HTTP_200_OK)