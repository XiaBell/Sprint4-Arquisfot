"""
URLs for Inventory Service
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health_check, name='health'),
    path('inventory/sql-list', views.sql_list, name='sql_list'),
    path('inventory/nosql-list', views.nosql_list, name='nosql_list'),
    path('inventory/stats', views.inventory_stats, name='inventory_stats'),
]

