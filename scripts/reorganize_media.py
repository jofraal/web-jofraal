#!/usr/bin/env python
"""
Script para reorganizar los archivos de mediafiles y corregir problemas de estructura.

Este script:
1. Corrige la carpeta 'barnds' mal escrita a 'brands'
2. Mueve los archivos a las carpetas correctas según su tipo
3. Actualiza las referencias en la base de datos si es necesario
"""

import os
import shutil
import django
import sys

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommercesite.settings.development')
django.setup()

from django.conf import settings
from products.models import Product, Brand, ProductVariant
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models.fields.files import ImageFieldFile

# Rutas de directorios
MEDIA_ROOT = settings.MEDIA_ROOT
BRANDS_DIR = os.path.join(MEDIA_ROOT, 'brands')
PRODUCTS_DIR = os.path.join(MEDIA_ROOT, 'products')
PRODUCT_VARIANTS_DIR = os.path.join(MEDIA_ROOT, 'product_variants')

# Asegurar que existan los directorios correctos
os.makedirs(BRANDS_DIR, exist_ok=True)
os.makedirs(PRODUCTS_DIR, exist_ok=True)
os.makedirs(PRODUCT_VARIANTS_DIR, exist_ok=True)

def fix_barnds_folder():
    """Corrige la carpeta 'barnds' mal escrita a 'brands'"""
    barnds_dir = os.path.join(MEDIA_ROOT, 'barnds')
    if os.path.exists(barnds_dir):
        print(f"Corrigiendo carpeta 'barnds' a 'brands'...")
        for filename in os.listdir(barnds_dir):
            src_path = os.path.join(barnds_dir, filename)
            dst_path = os.path.join(BRANDS_DIR, filename)
            if not os.path.exists(dst_path):
                shutil.copy2(src_path, dst_path)
                print(f"  Copiado: {filename} a la carpeta correcta 'brands/'")
        
        # No eliminamos la carpeta original para evitar problemas con referencias existentes
        print(f"La carpeta 'barnds' se ha mantenido para preservar compatibilidad.")

def identify_file_type(filename):
    """Identifica el tipo de archivo basado en su nombre y ubicación"""
    # Verificar si es un archivo de marca
    brands = Brand.objects.values_list('logo', flat=True)
    for brand_logo in brands:
        if brand_logo and os.path.basename(brand_logo.name) == filename:
            return 'brand'
    
    # Verificar si es un archivo de producto
    products = Product.objects.values_list('image', flat=True)
    for product_image in products:
        if product_image and os.path.basename(product_image.name) == filename:
            return 'product'
    
    # Verificar si es un archivo de variante de producto
    variants = ProductVariant.objects.values_list('image', flat=True)
    for variant_image in variants:
        if variant_image and os.path.basename(variant_image.name) == filename:
            return 'product_variant'
    
    # Si no se puede identificar, intentar adivinar por el nombre
    if 'shirt' in filename.lower() or 'jacket' in filename.lower():
        return 'product_variant'
    
    return 'unknown'

def reorganize_files():
    """Reorganiza los archivos en las carpetas correctas"""
    print("Reorganizando archivos...")
    
    # Lista de archivos en la raíz de mediafiles que no deberían estar ahí
    root_files = [f for f in os.listdir(MEDIA_ROOT) 
                 if os.path.isfile(os.path.join(MEDIA_ROOT, f)) and 
                 f != '.gitkeep']
    
    # Diccionario para almacenar las rutas originales y nuevas para actualizar la BD
    file_mappings = {}
    
    for filename in root_files:
        file_path = os.path.join(MEDIA_ROOT, filename)
        file_type = identify_file_type(filename)
        
        if file_type == 'brand':
            dst_path = os.path.join(BRANDS_DIR, filename)
            if not os.path.exists(dst_path):
                shutil.copy2(file_path, dst_path)
                print(f"  Movido: {filename} a brands/")
                file_mappings[filename] = f"brands/{filename}"
        
        elif file_type == 'product':
            dst_path = os.path.join(PRODUCTS_DIR, filename)
            if not os.path.exists(dst_path):
                shutil.copy2(file_path, dst_path)
                print(f"  Movido: {filename} a products/")
                file_mappings[filename] = f"products/{filename}"
        
        elif file_type == 'product_variant':
            dst_path = os.path.join(PRODUCT_VARIANTS_DIR, filename)
            if not os.path.exists(dst_path):
                shutil.copy2(file_path, dst_path)
                print(f"  Movido: {filename} a product_variants/")
                file_mappings[filename] = f"product_variants/{filename}"
        
        else:
            print(f"  No se pudo determinar el tipo de archivo: {filename}")
    
    # Actualizar las referencias en la base de datos
    if file_mappings:
        update_database_references(file_mappings)
    
    print("Los archivos originales se han mantenido para preservar compatibilidad.")
    print("Una vez verificado que todo funciona correctamente, puede eliminar manualmente los archivos duplicados.")
    
    # Verificar la integridad después de la reorganización
    verify_file_integrity()

def update_database_references(file_mappings):
    """Actualiza las referencias en la base de datos para que apunten a las nuevas ubicaciones"""
    print("\nActualizando referencias en la base de datos...")
    
    with transaction.atomic():
        # Actualizar referencias de marcas
        brands_updated = 0
        for brand in Brand.objects.all():
            if brand.logo and os.path.basename(brand.logo.name) in file_mappings:
                old_name = brand.logo.name
                new_path = file_mappings[os.path.basename(old_name)]
                # Solo actualizar si la ruta ha cambiado
                if old_name != new_path:
                    brand.logo.name = new_path
                    brand.save(update_fields=['logo'])
                    brands_updated += 1
                    print(f"  Actualizada referencia de marca: {brand.name} - {old_name} -> {new_path}")
        
        # Actualizar referencias de productos
        products_updated = 0
        for product in Product.objects.all():
            if product.image and os.path.basename(product.image.name) in file_mappings:
                old_name = product.image.name
                new_path = file_mappings[os.path.basename(old_name)]
                # Solo actualizar si la ruta ha cambiado
                if old_name != new_path:
                    product.image.name = new_path
                    product.save(update_fields=['image'])
                    products_updated += 1
                    print(f"  Actualizada referencia de producto: {product.name} - {old_name} -> {new_path}")
        
        # Actualizar referencias de variantes de productos
        variants_updated = 0
        for variant in ProductVariant.objects.all():
            if variant.image and os.path.basename(variant.image.name) in file_mappings:
                old_name = variant.image.name
                new_path = file_mappings[os.path.basename(old_name)]
                # Solo actualizar si la ruta ha cambiado
                if old_name != new_path:
                    variant.image.name = new_path
                    variant.save(update_fields=['image'])
                    variants_updated += 1
                    print(f"  Actualizada referencia de variante: {variant.product.name} ({variant.color}) - {old_name} -> {new_path}")
    
    print(f"\nActualización completada: {brands_updated} marcas, {products_updated} productos, {variants_updated} variantes")

def verify_file_integrity():
    """Verifica que todos los archivos referenciados existan en las ubicaciones correctas"""
    print("\nVerificando integridad de archivos...")
    
    missing_files = []
    
    # Verificar archivos de marcas
    for brand in Brand.objects.all():
        if brand.logo:
            file_path = os.path.join(MEDIA_ROOT, brand.logo.name)
            if not os.path.exists(file_path):
                missing_files.append(f"Marca '{brand.name}': {brand.logo.name}")
    
    # Verificar archivos de productos
    for product in Product.objects.all():
        if product.image:
            file_path = os.path.join(MEDIA_ROOT, product.image.name)
            if not os.path.exists(file_path):
                missing_files.append(f"Producto '{product.name}': {product.image.name}")
    
    # Verificar archivos de variantes de productos
    for variant in ProductVariant.objects.all():
        if variant.image:
            file_path = os.path.join(MEDIA_ROOT, variant.image.name)
            if not os.path.exists(file_path):
                missing_files.append(f"Variante '{variant.product.name} ({variant.color})': {variant.image.name}")
    
    if missing_files:
        print("\n¡ADVERTENCIA! Se encontraron archivos faltantes:")
        for missing in missing_files:
            print(f"  - {missing}")
        print("\nEs posible que necesite restaurar estos archivos o actualizar las referencias en la base de datos.")
    else:
        print("\nTodos los archivos referenciados existen en las ubicaciones correctas.")

def main():
    print("=== Iniciando reorganización de archivos de medios ===")
    fix_barnds_folder()
    reorganize_files()
    print("=== Reorganización completada ===\n")
    print("NOTA: Los archivos originales se han mantenido para evitar romper referencias existentes.")
    print("      Se recomienda verificar que todo funcione correctamente antes de eliminar los archivos duplicados.")

if __name__ == "__main__":
    main()