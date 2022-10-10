from django.urls import path
from .views.index import *
from .views.vaccines import *
from .views.analysis_population import Covariables as CovPop, Cells as CelPop, \
    CellsTimeValidation as CTVPop, ComputedCellsTimeValidation as CCTVPop, CovariablesDGE as CDGEPop, \
    CellsTimeValidationDGE as CTDGEPop
from .views.analysis import Covariables as Cov, CellsEnsamble as Cel
from .views.dge import Covariables as DGECov, Cells as DGECell, GetHistoricalProfile as GHP,\
    AvailableDateAnalysis as ADA, GetProfileCovariable as GPC, GetROCCurve as GROCC
from .views.data_nodes import DataNodes
#, Cells as Cel, CellsTimeValidation as CTV


urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('vaccines/', Vaccines.as_view(), name='vaccines'),
    path('vaccines/mesh/', Mesh.as_view(), name='mesh'),
    path('vaccines/target-groups/', TargetGroups.as_view(), name='target'),
    path('vaccines/summary-vaccines/', SummaryVaccines.as_view(), name='summary'),

    #path('utils/mesh/', Mesh.as_view(), name='mesh'),

    path('analysis-population/covariables/', CovPop.as_view(), name='cov_pop'),
    path('analysis-population/cells/', CelPop.as_view(), name='cel_pop'),    
    path('analysis-population/time-validation/', CTVPop.as_view(), name='ctv_pop'),

	path('analysis/covariables/', Cov.as_view(), name='cov'),
    #path('analysis/cells/', Cel.as_view(), name='cel'),    
    #path('analysis/time-validation/', CTV.as_view(), name='ctv'),    

    path('analysis-population/computed-time-validation/', CCTVPop.as_view(), name='cctv_pop'),

    path('nodes/', DataNodes.as_view(), name='data_nodes'),

    path('analysis-population/covariables-dge/', CDGEPop.as_view(), name='cov_dge_pop'),
    
    path('analysis/cells/', Cel.as_view(), name='cells_ensamble'),

    path('dge/covariables/', DGECov.as_view(), name='dge_covariables'),
    path('dge/cells/', DGECell.as_view(), name='dge_cells'),    
    path('dge/profile/', GHP.as_view(), name='dge_historical_profile'),    
    path('dge/available-date-analysis/', ADA.as_view(), name='available_date_analysis'), 
    path('dge/covariables/profile/', GPC.as_view(), name='dge_get_profile_covariable'),
    path('dge/roc/', GROCC.as_view(), name='dge_get_roc_curve'),   
]