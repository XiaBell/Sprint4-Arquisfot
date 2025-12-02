"""
URLs for Orders Service
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health_check, name='health'),
    path('orders', views.create_order, name='create_order'),
    path('orders/list', views.list_orders, name='list_orders'),
    path('orders/<int:order_id>', views.get_order, name='get_order'),
    path('orders/<int:order_id>/items/<int:item_id>', views.update_item_status, name='update_item_status'),
    path('orders/<int:order_id>/items/<int:item_id>/delete', views.delete_item, name='delete_item'),
]

