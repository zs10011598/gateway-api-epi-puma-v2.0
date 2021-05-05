from ..models.variable import *



def count_points(db, variable_id, mesh):
	'''
	'''
	c = Variable.objects.all().using(db).count()