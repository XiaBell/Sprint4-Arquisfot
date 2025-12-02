#!/usr/bin/env python
"""
Script para sincronizar todos los productos de PostgreSQL a MongoDB (CQRS)
Útil para sincronización inicial o resincronización completa
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_service.settings')
django.setup()

from inventory.models import Product
from inventory.mongodb_client import sync_product_to_mongodb

def sync_all_products():
    """Sincronizar todos los productos a MongoDB"""
    print("🔄 Sincronizando productos de PostgreSQL a MongoDB...")
    
    products = Product.objects.all()
    total = products.count()
    synced = 0
    failed = 0
    
    print(f"Total productos a sincronizar: {total}")
    
    for i, product in enumerate(products, 1):
        if sync_product_to_mongodb(product):
            synced += 1
        else:
            failed += 1
        
        if i % 1000 == 0:
            print(f"  Progreso: {i}/{total} - Sincronizados: {synced}, Fallidos: {failed}")
    
    print("\n" + "=" * 60)
    print("✅ SINCRONIZACIÓN COMPLETADA")
    print("=" * 60)
    print(f"Total procesados: {total}")
    print(f"✅ Sincronizados exitosamente: {synced}")
    print(f"❌ Fallidos: {failed}")

if __name__ == '__main__':
    sync_all_products()

