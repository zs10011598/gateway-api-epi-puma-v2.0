from ..models.cell import *
from ..serializers.cell import *
from ..models.occurrence import *
from collections import namedtuple 
from django.db.models import Sum



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


def get_irag_covariables_from_occurrences(occs):
    '''
    '''
    attributes_list = ['id', 'var', 'bin', 'cells_state', 'interval', 'cells_mun', 'cells_ageb']
    GenericCovariable = namedtuple('GenericCovariable', attributes_list) 
    covars = {}

    print('There are ' + str(len(occs)) + ' occurrences of IRAG covariables')

    for occ in occs:

        if not occ.variable_id in covars.keys(): 
            #print(occ)
            interval = OccurrenceIRAGInterval.objects.using('irag').get(variable_id=occ.variable_id, 
                                                                        date_occurrence=occ.date_occurrence).interval
            aux_covariable = GenericCovariable(id=occ.variable_id, var=occ.var, bin=occ.bin, cells_state=[occ.gridid_state], 
                                                interval=interval, cells_mun=[occ.gridid_mun], cells_ageb=[occ.gridid_ageb])
            covars[occ.variable_id] = aux_covariable
        elif not occ.gridid_mun in covars[occ.variable_id].cells_mun:
            covars[occ.variable_id].cells_mun.append(occ.gridid_mun)
            if not occ.gridid_state in covars[occ.variable_id].cells_state:
                covars[occ.variable_id].cells_state.append(occ.gridid_state)
            if not occ.gridid_ageb in covars[occ.variable_id].cells_ageb:
                covars[occ.variable_id].cells_ageb.append(occ.gridid_ageb)
    #print(covars.values())
    return covars.values()


def get_discretized_covars(occs, covars, mesh):
    p = 10

    covars_names = [cov['name'] for cov in covars.values('name').distinct()]
    #print('Covars names: ' + str(covars_names))
    list_occurrences = {}
    covars_tags = {}

    for name in covars_names:
        print('Discretizing: ' + name)
        occs_temp = occs.filter(var=name).values('gridid_' + mesh).annotate(value=Sum('value'))
        list_occurrences[name] = []
        covars_tags[name] = []
        #occs_temp = occs_temp.filter(var=name)
        N_occs = occs_temp.count()

        if N_occs == 0:
            print(name, ' no occurrences ')
            list_occurrences.pop(name, None)
            covars_tags.pop(name, None)
            continue

        #print('N_occs', N_occs)
        occs_temp = occs_temp.order_by('value')
        #print(occs_temp)
        limits = get_limits(N_occs, p)
        #print('limits ', limits)
        current_gridid_list = []
        currect_tags_list = []
        for i in range(p):
            current_gridid_list.append([occ['gridid_' + mesh] for occ in occs_temp[limits[i]: limits[i+1]]])
            currect_tags_list.append(str("%.4f" % round(occs_temp[limits[i]]['value'], 4)) + ':' + str("%.4f" % round(occs_temp[limits[i+1]]['value'], 4)))
        list_occurrences[name] = current_gridid_list
        covars_tags[name] = currect_tags_list

    #print(covars_tags)

    for covar in covars:
        if covar.name in list_occurrences.keys():
            setattr(covar, 'cells_' + mesh, list_occurrences[covar.name][covar.bin-1])
            setattr(covar, 'tag', covars_tags[covar.name][covar.bin-1])
        else:
            setattr(covar, 'cells_' + mesh, [])
            setattr(covar, 'tag', None)

    return covars


def get_limits(N, p):
    return [int(i*(N/p)) - int(i/p) for i in range(p+1)]
    