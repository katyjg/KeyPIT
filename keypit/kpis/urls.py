from django.urls import path

from . import views

urlpatterns = [
    path('departments/', views.DepartmentList.as_view(), name='department-list'),
    path('beamlines/', views.BeamlineList.as_view(), name='beamline-list'),
    path('kpis/', views.KPIList.as_view(), name='kpi-list'),
]