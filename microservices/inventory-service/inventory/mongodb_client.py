"""
MongoDB Client for Read Model (CQRS)
"""
from pymongo import MongoClient
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# MongoDB connection
_mongo_client = None
_mongo_db = None


def get_mongo_client():
    """Get or create MongoDB client"""
    global _mongo_client, _mongo_db
    
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(
                host=settings.MONGODB_HOST,
                port=settings.MONGODB_PORT,
                serverSelectionTimeoutMS=5000
            )
            _mongo_db = _mongo_client[settings.MONGODB_DB]
            # Test connection
            _mongo_client.server_info()
            logger.info(f"Connected to MongoDB at {settings.MONGODB_HOST}:{settings.MONGODB_PORT}")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise
    
    return _mongo_client, _mongo_db


def get_inventory_collection():
    """Get inventory collection from MongoDB"""
    _, db = get_mongo_client()
    return db['inventory']


def sync_product_to_mongodb(product):
    """
    Sincroniza un producto desde PostgreSQL (Write Model) a MongoDB (Read Model)
    """
    try:
        collection = get_inventory_collection()
        
        # Crear documento desnormalizado para lectura rápida
        document = {
            '_id': product.sku,
            'sku': product.sku,
            'name': product.name,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'unit_price': float(product.unit_price),
            'stock_quantity': product.stock_quantity,
            'min_stock_level': product.min_stock_level,
            'supplier': product.supplier,
            'created_at': product.created_at.isoformat(),
            'updated_at': product.updated_at.isoformat(),
        }
        
        # Upsert en MongoDB
        collection.replace_one(
            {'_id': product.sku},
            document,
            upsert=True
        )
        
        logger.info(f"Synced product {product.sku} to MongoDB")
        return True
    except Exception as e:
        logger.error(f"Error syncing product {product.sku} to MongoDB: {e}")
        return False

