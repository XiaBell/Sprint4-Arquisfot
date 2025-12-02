"""
Views for Inventory Service
"""
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from .mongodb_client import get_inventory_collection
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'ok',
        'service': 'inventory-service'
    })


@api_view(['GET'])
def sql_list(request):
    """
    Endpoint LENTO - Consulta compleja a PostgreSQL (Línea Base)
    Simula JOINs costosos para demostrar la diferencia con CQRS
    """
    start_time = time.time()
    
    try:
        with connection.cursor() as cursor:
            # Consulta compleja con JOINs (simulando operación costosa)
            query = """
                SELECT 
                    p.id,
                    p.sku,
                    p.name,
                    p.description,
                    p.unit_price,
                    p.stock_quantity,
                    p.min_stock_level,
                    p.supplier,
                    c.name as category_name,
                    c.description as category_description,
                    COUNT(it.id) as transaction_count
                FROM products p
                INNER JOIN product_categories c ON p.category_id = c.id
                LEFT JOIN inventory_transactions it ON p.id = it.product_id
                GROUP BY p.id, p.sku, p.name, p.description, p.unit_price, 
                         p.stock_quantity, p.min_stock_level, p.supplier,
                         c.name, c.description
                ORDER BY p.name
                LIMIT 10000
            """
            
            cursor.execute(query)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return Response({
            'data': results,
            'count': len(results),
            'elapsed_time_ms': round(elapsed_time, 2),
            'database': 'PostgreSQL',
            'query_type': 'Complex JOIN'
        })
    
    except Exception as e:
        logger.error(f"Error in sql_list: {e}")
        return Response({
            'error': str(e),
            'elapsed_time_ms': (time.time() - start_time) * 1000
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def nosql_list(request):
    """
    Endpoint RÁPIDO - Consulta simple a MongoDB (CQRS Optimizado)
    Documentos desnormalizados para lectura rápida
    """
    start_time = time.time()
    
    try:
        collection = get_inventory_collection()
        
        # Consulta simple y rápida a MongoDB
        # Los documentos ya están desnormalizados, no necesitamos JOINs
        cursor = collection.find({}).limit(10000).sort('name', 1)
        
        results = list(cursor)
        
        # Convertir ObjectId a string para JSON serialization
        for item in results:
            if '_id' in item:
                item['_id'] = str(item['_id'])
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return Response({
            'data': results,
            'count': len(results),
            'elapsed_time_ms': round(elapsed_time, 2),
            'database': 'MongoDB',
            'query_type': 'Simple Find (CQRS)'
        })
    
    except Exception as e:
        logger.error(f"Error in nosql_list: {e}")
        return Response({
            'error': str(e),
            'elapsed_time_ms': (time.time() - start_time) * 1000
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def inventory_stats(request):
    """Estadísticas del inventario desde MongoDB"""
    try:
        collection = get_inventory_collection()
        
        total_products = collection.count_documents({})
        low_stock = collection.count_documents({
            '$expr': {'$lt': ['$stock_quantity', '$min_stock_level']}
        })
        
        return Response({
            'total_products': total_products,
            'low_stock_items': low_stock,
            'database': 'MongoDB'
        })
    
    except Exception as e:
        logger.error(f"Error in inventory_stats: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

