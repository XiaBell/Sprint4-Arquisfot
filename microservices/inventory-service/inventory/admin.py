from django.contrib import admin
from .models import ProductCategory, Product, InventoryTransaction


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'category', 'stock_quantity', 'unit_price', 'supplier']
    list_filter = ['category', 'supplier']
    search_fields = ['sku', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['product', 'transaction_type', 'quantity', 'previous_stock', 'new_stock', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    readonly_fields = ['created_at']

