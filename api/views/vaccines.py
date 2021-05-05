from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models.cell import *
from ..models.target_group_population import *

from ..serializers.cell import *
from ..serializers.target_group_population import *


class Vaccines(APIView):

	def post(self, request):
		"""
			Description: Vaccines endpoint

		"""
		return Response({'message': 'Vaccines!'}, status=status.HTTP_200_OK)


class Mesh(APIView):

	def post(self, request):
		"""
			Description: Vaccines endpoint

		"""
		mesh = 'none'

		if 'mesh' in request.data.keys():
			mesh = request.data['mesh']

		cells = []
		message = 'OK'
		statusr = status.HTTP_200_OK

		if mesh == 'state':
			cells_state = CellState.objects.all()
			cells = [CellStateSerializer(c).data for c in cells_state]
		elif mesh == 'mun':
			cells_mun = CellMunicipality.objects.all()
			cells = [CellMunicipalitySerializer(c).data for c in cells_mun]
		elif mesh == 'ageb':
			cells_ageb = CellAGEB.objects.all()
			cells = [CellAGEBSerializer(c).data for c in cells_ageb]
		else:
			message = 'mesh {0} wasn\'t found'.format(mesh)
			statusr = status.HTTP_204_NO_CONTENT

		return Response({'message': message, 'cells': cells}, status=statusr)


class TargetGroups(APIView):
	
	def get(self, request):
		"""
			Description: Target Group endpoint

		"""

		target_groups = []
		message = 'OK'
		statusr = status.HTTP_200_OK

		try:
			target_group_models = TargetGroupCatalogue.objects.all()
			target_groups = [TargetGroupCatalogueSerializer(c).data for c in target_group_models]
		except Exception as e:
			message = str(e)
			statusr = status.HTTP_204_NO_CONTENT
		
		return Response({'message': message, 'target_groups': target_groups}, status=statusr)