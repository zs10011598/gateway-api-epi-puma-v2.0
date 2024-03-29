from ..models.cell import *
from ..serializers.cell import *
from ..models.occurrence import *
from ..models.variable import *
from collections import namedtuple 
from django.db.models import Sum, Count



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


def get_demographic_dge(mesh, demographic_group, target_filter):
    '''
    '''
    gridid = 'gridid_' + mesh
    filt = target_filter.copy()
    if demographic_group == 'p_60ymas':
        filt['edad__gte'] = 60
    elif demographic_group == 'p_50a59':
        filt['edad__gte'] = 50
        filt['edad__lte'] = 59
    elif demographic_group == 'p_40a49':
        filt['edad__gte'] = 40
        filt['edad__lte'] = 49
    elif demographic_group == 'p_30a39':
        filt['edad__gte'] = 30
        filt['edad__lte'] = 39
    elif demographic_group == 'p_18a29':
        filt['edad__gte'] = 18
        filt['edad__lte'] = 29

    qs = OccurrenceCOVID19.objects.using('covid19').\
            values('gridid_' + mesh).filter(**filt).annotate(tcount=Count('id'))

    demographic_map = {}

    for item in qs:
        demographic_map[item[gridid]] = item['tcount']

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


def get_discretized_covars(occs, covars, mesh, period=None):
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

        covar.name = covar.name + ('-' + str(period) if period != None else '')

    return [cov for cov in covars]


def get_limits(N, p):
    return [int(i*(N/p)) - int(i/p) for i in range(p+1)]


def get_modified_variables(occs, mesh, covar, modifier, p, map_cells_pobtot, backward_period, derivative=''):
    '''
    '''
    covars = []
    try:
        N = occs.count()
    except:
        N = len(occs)

    has_cases = False
    new_cells = []
    for cell in map_cells_pobtot.keys():
        for occ in occs:
            if occ['gridid_' + mesh] == cell:
                has_cases = True
                break

        if not has_cases:
            new_cells.append({'gridid_' + mesh: cell, 'tcount': 0})
        else:
            has_cases = False

    occs = [occ for occ in occs] + new_cells

    N += len(new_cells)
    limits = get_limits(N, p)
    
    if modifier == 'cases':
        pass
    elif modifier == 'incidence':
        for occ in occs:
            occ['tcount'] = occ['tcount']/map_cells_pobtot[occ['gridid_' + mesh]]

    for i in range(10):
        current_covar = VariableHistorical(id=int(str(backward_period)+str(10-i) + ('00100' if derivative == 'D' else ('00200' if derivative == 'D^2' else ''))), name=derivative + covar + '-' + modifier + '-' + str(backward_period), description=derivative + 'Periodo ' + str(backward_period), bin=10-i)
        setattr(current_covar, 'tag',  str(occs[limits[i]]['tcount']) + ':' + str(occs[limits[i+1]]['tcount']))
        cells_mun = []
        for occ in occs[limits[i]: limits[i+1]]:            
            cells_mun.append(occ['gridid_' + mesh])
        setattr(current_covar, 'cells_' + mesh, cells_mun)
        covars.append(current_covar)
    return covars


def get_historical_modified_variables(mesh, covars, backward_period=''):
    '''
    '''
    left_period = covars[20:]
    middle_period = covars[10:20]
    right_period = covars[:10]

    historical_covars = []

    for lp in left_period:
        for mp in middle_period:

            current_covar = VariableHistorical(id=int(backward_period + '3' + str(lp.bin) + '2' + str(mp.bin)), name=lp.name + '_' + mp.name, description='Periodo 3  Bin ' + str(lp.bin) + ' Periodo 2  Bin ' + str(mp.bin))

            cells_lp = getattr(lp, 'cells_' + mesh)
            cells_mp = getattr(mp, 'cells_' + mesh)

            cells_final = [clp for clp in cells_lp if clp in cells_mp]

            setattr(current_covar, 'cells_' + mesh, cells_final)

            if len(cells_final) > 0:
                historical_covars.append(current_covar)

    for lp in left_period:
        for rp in right_period:

            current_covar = VariableHistorical(id=int('3' + str(lp.bin) + '1' + str(rp.bin)), name=lp.name + '_' + rp.name, description='Periodo 3  Bin ' + str(lp.bin) + ' Periodo 1  Bin ' + str(rp.bin))

            cells_lp = getattr(lp, 'cells_' + mesh)
            cells_rp = getattr(rp, 'cells_' + mesh)

            cells_final = [clp for clp in cells_lp if lp in cells_rp]

            setattr(current_covar, 'cells_' + mesh, cells_final)

            if len(cells_final) > 0:
                historical_covars.append(current_covar)

    for mp in middle_period:
        for rp in right_period:

            current_covar = VariableHistorical(id=int('2' + str(mp.bin) + '1' + str(rp.bin)), name=mp.name + '_' + rp.name, description='Periodo 2  Bin ' + str(mp.bin) + ' Periodo 1  Bin ' + str(rp.bin))

            cells_mp = getattr(mp, 'cells_' + mesh)
            cells_rp = getattr(rp, 'cells_' + mesh)

            cells_final = [clp for clp in cells_mp if clp in cells_rp]

            setattr(current_covar, 'cells_' + mesh, cells_final)

            if len(cells_final) > 0:
                historical_covars.append(current_covar)

    for lp in left_period:
        for mp in middle_period:
            for rp in right_period:

                current_covar = VariableHistorical(id=int('3' + str(lp.bin) + '2' + str(mp.bin) + '1' + str(rp.bin)), name=lp.name + '_' + mp.name + '_' + rp.name, description='Periodo 3 Bin ' + str(lp.bin) + ' Periodo 2  Bin ' + str(mp.bin) + ' Periodo 1  Bin ' + str(rp.bin))
                
                cells_lp = getattr(lp, 'cells_' + mesh)
                cells_mp = getattr(mp, 'cells_' + mesh)
                cells_rp = getattr(rp, 'cells_' + mesh)

                cells_final = [clp for clp in cells_lp if clp in cells_mp and clp in cells_rp]

                setattr(current_covar, 'cells_' + mesh, cells_final)

                if len(cells_final) > 0:
                    historical_covars.append(current_covar)

    return historical_covars


def build_covariable_attribute(db, mesh, attribute, attribute_values, lim_inf, lim_sup, bins=10):
    """
        Description: get a covariable from attribute
    """
    attribute_filter = {'date_occurrence__lte': lim_sup, \
        'date_occurrence__gte': lim_inf, attribute + '__in': attribute_values}
    results = OccurrenceCOVID19.objects.using(db).values('gridid_' + mesh).\
        filter(**attribute_filter).annotate(tcount=Count('id')).order_by('-tcount')
    
    cells = get_mesh(mesh)
    cells_last_bin = {getattr(cell, 'gridid_' + mesh): False for cell in cells}
    
    tresults = {}
    bin_size = int(cells.count()/10)
    bins_list = []
    last_bin = 10
    for i in range(bins):
        bins_list.append({'name': attribute + '-' + str(10-i), 'cells_' + mesh: [], 'interval': ''})
        last_bin = i
        if results.count() - bin_size*i >= 0:
            pass
        else:
            break

    i = 0
    lim_sup = results[0]['tcount']
    lim_inf = results[0]['tcount']
    is_lim_sup = True
    for j in range(results.count()):
        if is_lim_sup:
            lim_sup = results[j]['tcount']
            is_lim_sup = False
        if j < (i+1)*bin_size:
            gridid = results[j]['gridid_' + mesh]
            bins_list[i]['cells_' + mesh].append(gridid)
            cells_last_bin[gridid] = True
        else:
            lim_inf = results[j]['tcount']
            bins_list[i]['interval'] = str(lim_inf) + ':' + str(lim_sup)
            i += 1
            is_lim_sup = True

    bins_list[-1]['interval'] = '0:0'
    for k in cells_last_bin.keys():
        if not cells_last_bin[k]:
            bins_list[-1]['cells_' + mesh].append(k)

    return bins_list