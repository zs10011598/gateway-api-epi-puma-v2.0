from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models.occurrence import *
import pandas as pd
from .analysis_population import get_target_filter
from ..utils.analysis import *
from ..serializers.cells_ensamble import EnsambleCellsRequest 
import json
from django.db.models import Q
import random


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


class CovariablesCellsEnsamble(APIView):

    def post(self, request):

        taxon_map_name = {
            'kingdom': 'reino', 
            'phylum': 'phylum', 
            'class': 'clase', 
            'order': 'orden', 
            'family': 'familia', 
            'genus': 'genero', 
            'species': 'nombrecientifico'
        }

        body = EnsambleCellsRequest(data=request.data)

        if body.is_valid():

            occs = []
            try:
                
                target = body.data['target']
                target_attribute_filter = body.data['target_attribute_filter']
                mesh = body.data['mesh']
                
                if 'agent' in target.keys():
                    if not target['agent'] in ['vector', 'hospedero', 'patogeno']:
                        return (None, '`agent doesn\'t allowed`')
                    else:
                        target_filter = {
                            taxon_map_name[target['species']['taxon']]: target['species']['value'],
                            'nombreenfermedad': target['disease']
                            }
                        target_filter = {
                            **target_filter, 
                            **query_map_builder(target_attribute_filter)}
                        #print(target_filter)
                        occs = OccurrenceEpiSpecies.objects.using(target['agent'])\
                            .values('gridid_' + mesh)\
                            .filter(**target_filter)\
                            .filter(~Q(**{'gridid_' + mesh: None}))\
                            .annotate(tcount=Sum('numeroindividuos'))\
                            .order_by()

            except Exception as e:
                print(str(e))
                return Response({'ok': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            epsilon_r = calculate_epsilon_cells_ensamble(
                body.data['covariables'], 
                body.data['covariable_filter'], 
                occs,
                body.data['mesh'])
        else:
            print(body.errors)
            return Response({'ok': False, 'message': body.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'ok': True, 'data': epsilon_r[0], 'message': epsilon_r[1]}, status=status.HTTP_200_OK)

class CellsEnsamble(APIView):

    def post(self, request):

        taxon_map_name = {
            'kingdom': 'reino', 
            'phylum': 'phylum', 
            'class': 'clase', 
            'order': 'orden', 
            'family': 'familia', 
            'genus': 'genero', 
            'species': 'nombrecientifico'
        }
        
        body = EnsambleCellsRequest(data=request.data)
        response = {}

        if body.is_valid():

            occs = []
            try:
                
                target = body.data['target']
                target_attribute_filter = body.data['target_attribute_filter']
                mesh = body.data['mesh']
                
                if 'agent' in target.keys():
                    if not target['agent'] in ['vector', 'hospedero', 'patogeno']:
                        return (None, '`agent doesn\'t allowed`')
                    else:
                        target_filter = {
                            taxon_map_name[target['species']['taxon']]: target['species']['value'],
                            'nombreenfermedad': target['disease']
                            }
                        target_filter = {
                            **target_filter, 
                            **query_map_builder(target_attribute_filter)}
                        #print(target_filter)
                        occs = OccurrenceEpiSpecies.objects\
                            .using(target['agent'])\
                            .values('gridid_' + mesh)\
                            .filter(**target_filter)\
                            .filter(~Q(**{'gridid_' + mesh: None}))\
                            .annotate(tcount=Sum('numeroindividuos'))\
                            .order_by()

                N_occs = occs.count()
                train_limit = int(N_occs*0.7)
                valid_limit = N_occs - train_limit
                occs_valid = random.sample(list(occs), k=valid_limit)
                occs_train = [occ for occ in occs if not occ in occs_valid]
            except Exception as e:
                print(str(e))
                return Response({'ok': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            data = calculate_epsilon_cells_ensamble(
                body.data['covariables'], 
                body.data['covariable_filter'], 
                occs_train,
                body.data['mesh'])

            #print(data)
            response['ok'] = True
            response['data'] = data[0]

            data_score_cell = calculate_score_cells_ensamble(data[0])
            response['data_score_cell'] = data_score_cell

            percentage_avg = caculate_decil_info(data[0], data_score_cell, 10)
            response['percentage_avg'] = percentage_avg            

            validation_data = validation_data_analysis(mesh, occs_valid, data_score_cell)
            response['validation_data'] = validation_data            
            
        else:
            print(body.errors)
            return Response({'ok': False, 'message': body.errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response, status=status.HTTP_200_OK)