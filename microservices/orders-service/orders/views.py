"""
Views for Orders Service
"""
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Order, OrderItem
from .middleware import require_gestor_role, optional_auth
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'ok',
        'service': 'orders-service'
    })


@api_view(['POST'])
def create_order(request):
    """
    Crear un nuevo pedido
    No requiere rol específico (cualquier usuario autenticado puede crear pedidos)
    """
    try:
        data = request.data
        
        # Generar número de orden único
        import uuid
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        order = Order.objects.create(
            order_number=order_number,
            customer_name=data.get('customer_name', ''),
            customer_email=data.get('customer_email', ''),
            customer_company=data.get('customer_company', ''),
            notes=data.get('notes', ''),
            created_by=getattr(request, 'user_id', None)
        )
        
        # Crear ítems del pedido
        items_data = data.get('items', [])
        for item_data in items_data:
            OrderItem.objects.create(
                order=order,
                product_sku=item_data.get('product_sku'),
                product_name=item_data.get('product_name'),
                quantity=item_data.get('quantity', 1),
                unit_price=item_data.get('unit_price', 0),
            )
        
        order.calculate_total()
        
        return Response({
            'id': order.id,
            'order_number': order.order_number,
            'status': order.status,
            'total_amount': str(order.total_amount),
            'created_at': order.created_at.isoformat()
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@optional_auth
def get_order(request, order_id):
    """
    Obtener detalles de un pedido
    Permite acceso a ambos roles (GESTOR y OPERARIO) para lectura
    """
    try:
        order = get_object_or_404(Order, id=order_id)
        
        items = []
        for item in order.items.all():
            items.append({
                'id': item.id,
                'product_sku': item.product_sku,
                'product_name': item.product_name,
                'quantity': item.quantity,
                'unit_price': str(item.unit_price),
                'subtotal': str(item.subtotal),
                'status': item.status,
                'notes': item.notes,
            })
        
        return Response({
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'customer_email': order.customer_email,
            'customer_company': order.customer_company,
            'status': order.status,
            'total_amount': str(order.total_amount),
            'notes': order.notes,
            'items': items,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
        })
    
    except Exception as e:
        logger.error(f"Error getting order: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@require_gestor_role
def update_item_status(request, order_id, item_id):
    """
    Marcar ítem como no disponible o cambiar su estado
    REQUIERE ROL: GESTOR
    """
    start_time = time.time()
    
    try:
        order = get_object_or_404(Order, id=order_id)
        item = get_object_or_404(OrderItem, id=item_id, order=order)
        
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(OrderItem.ITEM_STATUS):
            return Response({
                'error': f'Invalid status. Must be one of: {list(dict(OrderItem.ITEM_STATUS).keys())}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        item.status = new_status
        if notes:
            item.notes = notes
        item.save()
        
        elapsed_time = (time.time() - start_time) * 1000
        
        return Response({
            'id': item.id,
            'product_sku': item.product_sku,
            'status': item.status,
            'notes': item.notes,
            'updated_at': item.updated_at.isoformat(),
            'elapsed_time_ms': round(elapsed_time, 2),
            'validation_time_ms': getattr(request, 'validation_time_ms', 0)
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Error updating item status: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@require_gestor_role
def delete_item(request, order_id, item_id):
    """
    Eliminar ítem de un pedido
    REQUIERE ROL: GESTOR
    """
    start_time = time.time()
    
    try:
        order = get_object_or_404(Order, id=order_id)
        item = get_object_or_404(OrderItem, id=item_id, order=order)
        
        item.delete()
        order.calculate_total()
        
        elapsed_time = (time.time() - start_time) * 1000
        
        return Response({
            'message': 'Item deleted successfully',
            'elapsed_time_ms': round(elapsed_time, 2),
            'validation_time_ms': getattr(request, 'validation_time_ms', 0)
        }, status=status.HTTP_204_NO_CONTENT)
    
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@optional_auth
def list_orders(request):
    """Listar todos los pedidos"""
    try:
        orders = Order.objects.all()[:50]  # Limit to 50 for demo
        
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'status': order.status,
                'total_amount': str(order.total_amount),
                'created_at': order.created_at.isoformat(),
            })
        
        return Response({
            'orders': orders_data,
            'count': len(orders_data)
        })
    
    except Exception as e:
        logger.error(f"Error listing orders: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

