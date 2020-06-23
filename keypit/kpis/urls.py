from django.urls import path

from . import views

urlpatterns = [
    path('<int:year>/<str:period>/', views.Dashboard.as_view(), name='all-year'),

    path('departments/', views.DepartmentList.as_view(), name='department-list'),
    path('departments/<int:pk>/', views.DepartmentDetail.as_view(), name='department-detail'),
    path('departments/<int:pk>/<int:year>/<str:period>/', views.DepartmentDetail.as_view(), name='department-year'),
    path('departments/new/', views.DepartmentCreate.as_view(), name='new-department'),
    path('departments/<int:pk>/edit/', views.DepartmentEdit.as_view(), name='department-edit'),

    path('beamlines/', views.BeamlineList.as_view(), name='beamline-list'),
    path('beamlines/<int:pk>/', views.BeamlineDetail.as_view(), name='beamline-detail'),
    path('beamlines/<int:pk>/<int:year>/<str:period>/', views.BeamlineDetail.as_view(), name='beamline-year'),
    path('beamlines/<int:pk>/<int:year>/month/<int:month>/', views.BeamlineMonth.as_view(), name='beamline-month'),
    path('beamlines/<int:pk>/<int:year>/quarter/<int:quarter>/', views.BeamlineQuarter.as_view(), name='beamline-quarter'),
    path('beamlines/<int:pk>/new-month/', views.BeamlineCreateMonth.as_view(), name='new-month'),
    path('beamlines/<int:pk>/<int:year>/<int:month>/new/', views.BeamlineCreateThisMonth.as_view(), name='new-this-month'),
    path('beamlines/new/', views.BeamlineCreate.as_view(), name='new-beamline'),
    path('beamlines/<int:pk>/edit/', views.BeamlineEdit.as_view(), name='beamline-edit'),

    path('categories/', views.KPICategoryList.as_view(), name='category-list'),
    path('categories/new/', views.KPICategoryCreate.as_view(), name='new-category'),
    path('categories/<int:pk>/edit/', views.KPICategoryEdit.as_view(), name='category-edit'),

    path('kpis/', views.KPIList.as_view(), name='kpi-list'),
    path('kpis/new/', views.KPICreate.as_view(), name='new-kpi'),
    path('kpis/<int:pk>/', views.KPIDetail.as_view(), name='kpi-detail'),
    path('kpis/<int:pk>/<int:year>/<str:period>/', views.KPIDetail.as_view(), name='kpi-year'),
    path('kpis/<int:pk>/edit/', views.KPIEdit.as_view(), name='kpi-edit'),

    path('entries/<int:pk>/edit/', views.KPIEntryEdit.as_view(), name='kpientry-edit'),
]