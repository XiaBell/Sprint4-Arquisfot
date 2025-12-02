#!/usr/bin/env python
"""
Script para poblar la base de datos con 100,000 productos de inventario
y sincronizarlos a MongoDB (CQRS)
"""
import os
import sys
import django
from faker import Faker
import random
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_service.settings')
django.setup()

from inventory.models import ProductCategory, Product, InventoryTransaction
from inventory.mongodb_client import sync_product_to_mongodb

fake = Faker('es_ES')

# Categorías de productos de seguridad
CATEGORIES = [
    'Guantes de Seguridad',
    'Señalizaciones',
    'Cascos de Protección',
    'Gafas de Seguridad',
    'Calzado de Seguridad',
    'Chalecos Reflectantes',
    'Extintores',
    'Botiquines',
    'Cintas de Seguridad',
    'Conos de Tráfico'
]

# Tipos de productos por categoría
PRODUCT_TYPES = {
    'Guantes de Seguridad': ['Guantes Nitrilo', 'Guantes Látex', 'Guantes Cuero', 'Guantes Anticorte'],
    'Señalizaciones': ['Señal Prohibido', 'Señal Advertencia', 'Señal Obligatorio', 'Señal Información'],
    'Cascos de Protección': ['Casco Clase A', 'Casco Clase B', 'Casco Clase C', 'Casco con Visera'],
    'Gafas de Seguridad': ['Gafas Anti-Vaho', 'Gafas Anti-Rayos UV', 'Gafas de Seguridad Básicas'],
    'Calzado de Seguridad': ['Botas de Seguridad', 'Zapatos de Seguridad', 'Botas Impermeables'],
    'Chalecos Reflectantes': ['Chaleco Clase 2', 'Chaleco Clase 3', 'Chaleco con Bolsillos'],
    'Extintores': ['Extintor ABC', 'Extintor CO2', 'Extintor Agua', 'Extintor Polvo'],
    'Botiquines': ['Botiquín Básico', 'Botiquín Completo', 'Botiquín Industrial'],
    'Cintas de Seguridad': ['Cinta Amarilla', 'Cinta Roja', 'Cinta Blanca', 'Cinta Reflectante'],
    'Conos de Tráfico': ['Cono 45cm', 'Cono 60cm', 'Cono 75cm', 'Cono con Luz']
}

def create_categories():
    """Crear categorías de productos"""
    categories = {}
    for cat_name in CATEGORIES:
        category, created = ProductCategory.objects.get_or_create(
            name=cat_name,
            defaults={'description': f'Categoría de {cat_name.lower()}'}
        )
        categories[cat_name] = category
        print(f"✓ Categoría creada: {cat_name}")
    return categories

def generate_product_sku(category_name, product_type, index):
    """Generar SKU único"""
    category_code = ''.join([c[0].upper() for c in category_name.split()[:2]])
    product_code = ''.join([c[0].upper() for c in product_type.split()[:2]])
    return f"{category_code}-{product_code}-{index:06d}"

def create_products(categories, num_products=100000):
    """Crear productos y sincronizarlos a MongoDB"""
    print(f"\n📦 Creando {num_products} productos...")
    
    created = 0
    synced = 0
    
    for i in range(num_products):
        # Seleccionar categoría aleatoria
        category_name = random.choice(CATEGORIES)
        category = categories[category_name]
        
        # Seleccionar tipo de producto
        product_type = random.choice(PRODUCT_TYPES[category_name])
        
        # Generar SKU único
        sku = generate_product_sku(category_name, product_type, i)
        
        # Crear producto
        product = Product.objects.create(
            sku=sku,
            name=f"{product_type} {fake.word().capitalize()}",
            description=fake.text(max_nb_chars=200),
            category=category,
            unit_price=Decimal(str(round(random.uniform(5.00, 500.00), 2))),
            stock_quantity=random.randint(0, 1000),
            min_stock_level=random.randint(5, 50),
            supplier=fake.company()
        )
        
        created += 1
        
        # Sincronizar a MongoDB (CQRS)
        if sync_product_to_mongodb(product):
            synced += 1
        
        # Mostrar progreso cada 1000 productos
        if (i + 1) % 1000 == 0:
            print(f"  Progreso: {i + 1}/{num_products} productos creados, {synced} sincronizados a MongoDB")
    
    print(f"\n✅ Completado: {created} productos creados en PostgreSQL")
    print(f"✅ Sincronizados: {synced} productos en MongoDB (CQRS)")
    
    return created, synced

def create_transactions(products, num_transactions=10000):
    """Crear transacciones de inventario para auditoría"""
    print(f"\n📝 Creando {num_transactions} transacciones...")
    
    created = 0
    for _ in range(num_transactions):
        product = random.choice(products)
        transaction_type = random.choice(['IN', 'OUT', 'ADJ'])
        quantity = random.randint(1, 100)
        
        previous_stock = product.stock_quantity
        if transaction_type == 'IN':
            new_stock = previous_stock + quantity
        elif transaction_type == 'OUT':
            new_stock = max(0, previous_stock - quantity)
        else:  # ADJ
            new_stock = previous_stock + random.randint(-50, 50)
        
        InventoryTransaction.objects.create(
            product=product,
            transaction_type=transaction_type,
            quantity=quantity,
            previous_stock=previous_stock,
            new_stock=new_stock,
            notes=fake.sentence()
        )
        
        # Actualizar stock del producto
        product.stock_quantity = new_stock
        product.save()
        
        created += 1
        
        if created % 1000 == 0:
            print(f"  Progreso: {created}/{num_transactions} transacciones creadas")
    
    print(f"✅ {created} transacciones creadas")
    return created

def main():
    print("=" * 60)
    print("🚀 POBLACIÓN DE BASE DE DATOS - PROVESI")
    print("=" * 60)
    
    # Crear categorías
    print("\n📂 Creando categorías...")
    categories = create_categories()
    
    # Crear productos
    num_products = 100000
    created, synced = create_products(categories, num_products)
    
    # Crear algunas transacciones
    print("\n📊 Creando transacciones de inventario...")
    products = list(Product.objects.all()[:1000])  # Tomar muestra para transacciones
    create_transactions(products, 10000)
    
    print("\n" + "=" * 60)
    print("✅ POBLACIÓN COMPLETADA")
    print("=" * 60)
    print(f"Total productos en PostgreSQL: {Product.objects.count()}")
    print(f"Total categorías: {ProductCategory.objects.count()}")
    print(f"Total transacciones: {InventoryTransaction.objects.count()}")
    print("\n💡 Nota: Verificar sincronización en MongoDB manualmente")

if __name__ == '__main__':
    main()

