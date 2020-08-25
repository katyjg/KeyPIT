from django.urls import path

from . import views

urlpatterns = [
    path('', views.Dashboard.as_view(), name='dashboard'),
    path('<int:year>/<str:period>/', views.Dashboard.as_view(), name='all-year'),

    path('units/', views.UnitList.as_view(), name='unit-list'),
    path('units/<int:pk>/', views.UnitDetail.as_view(), name='unit-detail'),
    path('units/<int:pk>/<int:year>/<str:period>/', views.UnitDetail.as_view(), name='unit-year'),
    path('units/<int:pk>/<int:year>/month/<int:month>/', views.UnitReport.as_view(), name='unit-report'),
    path('units/new/', views.UnitCreate.as_view(), name='new-unit'),
    path('units/<int:pk>/edit/', views.UnitEdit.as_view(), name='unit-edit'),

    path('categories/', views.KPICategoryList.as_view(), name='category-list'),
    path('categories/new/', views.KPICategoryCreate.as_view(), name='new-category'),
    path('categories/<int:pk>/edit/', views.KPICategoryEdit.as_view(), name='category-edit'),

    path('kpis/', views.KPIList.as_view(), name='kpi-list'),
    path('kpis/new/', views.KPICreate.as_view(), name='new-kpi'),
    path('kpis/<int:pk>/', views.KPIDetail.as_view(), name='kpi-detail'),
    path('kpis/<int:pk>/<int:year>/<str:period>/', views.KPIDetail.as_view(), name='kpi-year'),
    path('kpis/<int:pk>/edit/', views.KPIEdit.as_view(), name='kpi-edit'),

    path('entries/new/', views.KPIEntryCreate.as_view(), name='kpientry-new'),
    path('entries/<int:pk>/edit/', views.KPIEntryEdit.as_view(), name='kpientry-edit'),
]