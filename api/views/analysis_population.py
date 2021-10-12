from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..utils.analysis_population import *
from ..utils.aggregation import *
from ..models.occurrence import *
import pandas as pd



class Covariables(APIView):

	def post(self, request):
		"""
			
		"""
		if 'covariables' in request.data.keys():
			dbs = request.data['covariables']
		else:
			return Response({"message": "`covariables` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'covariable_filter' in request.data.keys():
			covariable_filter = request.data['covariable_filter']
		else:
			covariable_filter = {}

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

		computations  = calculate_epsilon(dbs, covariable_filter, target_filter, mesh, target, demographic_group)

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


class Cells(APIView):

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

		response = response = calculate_score(dbs, mesh, target, lim_inf_training, lim_sup_training) 
		return Response({'data': response}, status=status.HTTP_200_OK)


class CellsTimeValidation(APIView):

	def post(self, request):
		"""
			
		"""
		if 'covariables' in request.data.keys():
			dbs = request.data['covariables']
		else:
			return Response({"message": "`covariables` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'covariable_filter' in request.data.keys():
			covariable_filter = request.data['covariable_filter']
		else:
			covariable_filter = {}		

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
			return Response({"message": "`lim_inf_training` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'lim_sup_training' in request.data.keys():
			lim_sup_training = request.data['lim_sup_training']
		else:
			return Response({"message": "`lim_sup_training` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'lim_inf_first' in request.data.keys():
			lim_inf_first = request.data['lim_inf_first']
		else:
			return Response({"message": "`lim_inf_first` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'lim_sup_first' in request.data.keys():
			lim_sup_first = request.data['lim_sup_first']
		else:
			return Response({"message": "`lim_sup_first` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'lim_inf_validation' in request.data.keys():
			lim_inf_validation = request.data['lim_inf_validation']
		else:
			return Response({"message": "`lim_inf_validation` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)			

		if 'lim_sup_validation' in request.data.keys():
			lim_sup_validation = request.data['lim_sup_validation']
		else:
			return Response({"message": "`lim_sup_validation` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

		if 'attribute_filter' in request.data.keys():
			attribute_filter = request.data['attribute_filter']
		else:
			attribute_filter = {}

		if 'demographic_group' in request.data.keys():
			demographic_group = request.data['demographic_group']
		else:
			demographic_group = None

		#print(attribute_filter)

		#print(map_target_validation)
		response = calculate_score(dbs, covariable_filter, mesh, target, lim_inf_training, lim_sup_training, 
									lim_inf_first, lim_sup_first, 
									lim_inf_validation, lim_sup_validation, demographic_group,
									attribute_filter) 

		return Response({'data': response}, status=status.HTTP_200_OK)