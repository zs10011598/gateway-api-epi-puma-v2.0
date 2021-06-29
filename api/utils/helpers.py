from ..models.cell import *
from ..serializers.cell import *
from ..models.occurrence import *



def mesh_occurrence_condition(mesh, filter_cond):
    '''
    '''
    if mesh == 'state':
        filter_cond['gridid_mun'] = -99999
    elif mesh == 'mun':
        filter_cond['gridid_ageb'] = -99999
    else:
        filter_cond['gridid_ageb__ne'] = -99999

    return filter_cond


def get_mesh(mesh):
    '''
    '''
    cells = []
    if mesh == 'state':
        cells = CellState.objects.all()
    elif mesh == 'mun':
        cells = CellMunicipality.objects.all()
    else:
        cells = CellAGEB.objects.all()
    return cells


def get_serialized_cell(cell, mesh):
    '''
    '''
    if mesh == 'state':
        return CellStateSerializer(cell).data
    elif mesh == 'mun':
        return CellMunicipalitySerializer(cell).data
    else:
        return CellAGEBSerializer(cell).data


def make_map(qs, key, value):
    '''
    '''
    map_qs = {}
    for item in qs:
        map_qs[item[key]] = item[value]
    return map_qs


def get_demographic(mesh, demographic_group):
    '''
    '''
    gridid = 'gridid_' + mesh

    qs = OccurrenceINEGI2020.objects.using('inegi2020').values(gridid, demographic_group, 'pobtot').distinct()
    demographic_map = {}

    for item in qs:
        demographic_map[item[gridid]] = item[demographic_group]*item['pobtot']

    return demographic_map


def query_map_builder(l):
    '''
    '''
    query_map = {}
    query_operator = ''
    for item in l:
        if item['operator'] == '>':
            query_operator = '__gt'
        elif item['operator'] == '==':
            query_operator = ''
        elif item['operator'] == '>=':
            query_operator = '__gte'
        elif item['operator'] == '<=':
            query_operator = '__lte'
        elif item['operator'] == '<':
            query_operator = '__lt'
        query_map[item['attribute'] + query_operator] = item['value']
    #print(query_map)
    return query_map
