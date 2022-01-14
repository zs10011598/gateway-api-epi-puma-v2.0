from ..models.occurrence import *
from django.db.models import Sum, Count


def get_target_deciles(node, mesh, target, target_filter, day):
    '''
        Description: get deciles from a node in specific date

        Args:
            - node
            - mesh
            - target
            - target_filter
            - date to consider
            - modifier: 'no_cases', 'incidence'

        Return:
            Covariable list of computed deciles  
    '''

    target_filter['date_occurrence'] = day

    if target == 'VACUNADO':
        target_by_cell = OccurrenceVaccines.objects.using('vaccines').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))
    else:
        target_by_cell = OccurrenceCOVID19.objects.using('covid19').values('gridid_' + mesh).filter(**target_filter).annotate(tcount=Count('id'))

    target_by_cell = target_by_cell.order_by('-tcount')

    
    
    return target_by_cell
