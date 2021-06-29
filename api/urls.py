from django.urls import path
from .views.index import *
from .views.vaccines import *
from .views.analysis_population import Covariables as CovPop, Cells as CelPop, CellsTimeValidation as CTVPop



urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('vaccines/', Vaccines.as_view(), name='vaccines'),
    path('vaccines/mesh/', Mesh.as_view(), name='mesh'),
    path('vaccines/target-groups/', TargetGroups.as_view(), name='target'),
    path('vaccines/summary-vaccines/', SummaryVaccines.as_view(), name='summary'),

    #path('utils/mesh/', Mesh.as_view(), name='mesh'),

    path('analysis-population/covariables/', CovPop.as_view(), name='cov_pop'),
    path('analysis-population/cells/', CelPop.as_view(), name='cov_pop'),    
    path('analysis-population/time-validation/', CTVPop.as_view(), name='ctv_pop'),
]