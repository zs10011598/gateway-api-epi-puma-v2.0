from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models.cell import *
from ..models.target_group_population import *

from ..serializers.cell import *
from ..serializers.target_group_population import *

from ..utils.helpers import *
from ..utils.analysis_population import *

from ..models.occurrence import *


class Vaccines(APIView):

    def post(self, request):
        """
            Description: Vaccines endpoint

        """
        return Response({'message': 'Vaccines!'}, status=status.HTTP_200_OK)


class SummaryVaccines(APIView):

    def post(self, request):
        """
            Description: Vaccines endpoint

        """

        if 'mesh' in request.data.keys():
            mesh = request.data['mesh']
        else:
            return Response({"message": "`mesh` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

        if 'lim_inf_training' in request.data.keys():
            lim_inf_training = request.data['lim_inf_training']
        else:
            return Response({"message": "`lim_inf_training` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

        if 'lim_sup_training' in request.data.keys():
            lim_sup_training = request.data['lim_sup_training']
        else:
            return Response({"message": "`lim_sup_training` parameter not found"}, status=status.HTTP_400_BAD_REQUEST)
        
        if 'attribute_filter' in request.data.keys():
            attribute_filter = request.data['attribute_filter']
        else:
            attribute_filter = {}

        if 'demographic_group' in request.data.keys():
            demographic_group = request.data['demographic_group']
        else:
            demographic_group = None

        summary_vaccines_list = []

        demographic_group_dict = {}
        if demographic_group != None:
            demographic_group_dict = get_demographic(mesh, demographic_group)

        cells = get_mesh(mesh)
        target_filter = get_target_filter(mesh, lim_inf_training, lim_sup_training, 'VACUNADO', attribute_filter)
        target_training = OccurrenceVaccines.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter).annotate(count=Count('id'))

        cummulated_filter = get_target_filter(mesh, '2021-01-01', lim_sup_training, 'VACUNADO', attribute_filter)
        cummulated_training = OccurrenceVaccines.objects.using('vaccines').values('gridid_' + mesh).filter(**cummulated_filter).annotate(count=Count('id'))

        target_training_map = {}
        for item in target_training:
            target_training_map[item['gridid_' + mesh]] = item['count']

        cummulated_training_map = {}
        for item in cummulated_training:
            cummulated_training_map[item['gridid_' + mesh]] = item['count']

        current_cell = {}

        for gridid in demographic_group_dict:
            count = target_training_map[gridid] if gridid in target_training_map.keys() else 0
            cummulated_count = cummulated_training_map[gridid] if gridid in cummulated_training_map.keys() else 0
            summary_vaccines_list.append({demographic_group: int(demographic_group_dict[gridid]), 
                                          'count': count, 
                                          'gridid': gridid,
                                          'percentage_vaccinated': (count/demographic_group_dict[gridid])*100,
                                          'cummulated_count': cummulated_count,
                                          'percentage_cummulated': (cummulated_count/demographic_group_dict[gridid])*100})

        return Response({'summary_vaccines': summary_vaccines_list}, status=status.HTTP_200_OK)


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