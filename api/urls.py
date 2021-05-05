from django.urls import path
from .views.index import *
from .views.vaccines import *



urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('vaccines/', Vaccines.as_view(), name='vaccines'),
    path('vaccines/mesh/', Mesh.as_view(), name='mesh'),
    path('vaccines/target-groups/', TargetGroups.as_view(), name='target'),
]