from ..models.variable import *
from ..models.occurrence import *
from django.db.models import Q
from .helpers import *



def count_occurrences_by_variable(db, variable_id, mesh, query=None, inf_date=None, sup_date=None):
	'''
	'''
	if query == None:
		filter_cond = {'variable_id': variable_id}
	else:
		filter_cond = query
		filter_cond['variable_id'] = variable_id

	filter_cond = mesh_occurrence_condition(mesh, filter_cond)	

	if inf_date != None:
		filter_cond['date_occurrence__gte'] = inf_date

	if sup_date != None:
		filter_cond['date_occurrence__lte'] = sup_date

	print(filter_cond)

	occ_count = Occurrence.objects.using(db).filter(**filter_cond).count()
	return occ_count