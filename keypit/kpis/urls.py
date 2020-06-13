from django.urls import path

from . import views

urlpatterns = [
    path('departments/', views.DepartmentList.as_view(), name='department-list'),
    path('department/<int:pk>/', views.DepartmentDetail.as_view(), name='department-detail'),
    path('beamlines/', views.BeamlineList.as_view(), name='beamline-list'),
    path('beamlines/<int:pk>/', views.BeamlineDetail.as_view(), name='beamline-detail'),
    path('beamlines/<int:pk>/<int:year>/<int:month>/', views.BeamlineReport.as_view(), name='beamline-report'),
    path('beamlines/new-report/', views.KPIEntryCreate.as_view(), name='new-beamline-report'),
    path('kpis/', views.KPIList.as_view(), name='kpi-list'),
    path('kpis/<int:pk>/', views.KPIDetail.as_view(), name='kpi-detail'),

    path('kpis/new/', views.KPICreate.as_view(), name='new-kpi'),
    path('kpis/<int:pk>/edit/', views.KPIEdit.as_view(), name='kpi-edit'),

    path('entries/new/', views.KPIEntryCreate.as_view(), name='new-kpientry'),
    path('entries/<int:pk>/edit/', views.KPIEntryEdit.as_view(), name='kpientry-edit'),
]