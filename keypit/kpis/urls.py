from django.urls import path

from . import views

urlpatterns = [
    path('<int:year>/', views.Dashboard.as_view(), name='all-year'),

    path('departments/', views.DepartmentList.as_view(), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentDetail.as_view(), name='department-detail'),
    path('departments/<int:pk>/<int:year>/', views.DepartmentDetail.as_view(), name='department-year'),
    path('beamlines/', views.BeamlineList.as_view(), name='beamline-list'),
    path('beamlines/<int:pk>/', views.BeamlineDetail.as_view(), name='beamline-detail'),
    path('beamlines/<int:pk>/<int:year>/', views.BeamlineDetail.as_view(), name='beamline-year'),
    path('beamlines/<int:pk>/<int:year>/<int:month>/', views.BeamlineMonth.as_view(), name='beamline-month'),
    path('beamlines/<int:pk>/<int:year>/<int:month>/new/', views.KPIEntryCreate.as_view(), name='new-beamline-month'),
    path('kpis/', views.KPIList.as_view(), name='kpi-list'),
    path('kpis/new/', views.KPICreate.as_view(), name='new-kpi'),
    path('kpis/<int:pk>/', views.KPIDetail.as_view(), name='kpi-detail'),
    path('kpis/<int:pk>/<int:year>/', views.KPIDetail.as_view(), name='kpi-year'),
    path('kpis/<int:pk>/edit/', views.KPIEdit.as_view(), name='kpi-edit'),

    path('entries/<int:pk>/new/', views.BeamlineMonthCreate.as_view(), name='new-month'),
    path('entries/<int:pk>/edit/', views.KPIEntryEdit.as_view(), name='kpientry-edit'),
]