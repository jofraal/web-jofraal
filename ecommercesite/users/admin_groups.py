from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from products.models import Product, ProductVariant, Category, Brand
from orders.models import Order
from core.models import Reclamacion, NewsletterSubscriber
from users.models import Profile

def create_admin_groups():
    """
    Creates predefined admin groups with different permission levels.
    
    This function creates the following admin groups:
    1. SuperAdmins - Full access to all models
    2. ProductManagers - Can manage products, variants, categories, and brands
    3. OrderManagers - Can view and manage orders
    4. CustomerSupportManagers - Can handle customer complaints and support
    """
    
    # Create the groups if they don't exist
    super_admins, _ = Group.objects.get_or_create(name='SuperAdmins')
    product_managers, _ = Group.objects.get_or_create(name='ProductManagers')
    order_managers, _ = Group.objects.get_or_create(name='OrderManagers')
    customer_support, _ = Group.objects.get_or_create(name='CustomerSupportManagers')
    
    # Clear existing permissions to avoid duplicates
    super_admins.permissions.clear()
    product_managers.permissions.clear()
    order_managers.permissions.clear()
    customer_support.permissions.clear()
    
    # Get content types for each model
    product_ct = ContentType.objects.get_for_model(Product)
    product_variant_ct = ContentType.objects.get_for_model(ProductVariant)
    category_ct = ContentType.objects.get_for_model(Category)
    brand_ct = ContentType.objects.get_for_model(Brand)
    order_ct = ContentType.objects.get_for_model(Order)
    reclamacion_ct = ContentType.objects.get_for_model(Reclamacion)
    newsletter_ct = ContentType.objects.get_for_model(NewsletterSubscriber)
    profile_ct = ContentType.objects.get_for_model(Profile)
    
    # Get all permissions
    all_permissions = Permission.objects.all()
    
    # Assign all permissions to SuperAdmins
    super_admins.permissions.add(*all_permissions)
    
    # Assign product-related permissions to ProductManagers
    product_permissions = Permission.objects.filter(
        content_type__in=[
            product_ct, product_variant_ct, category_ct, brand_ct
        ]
    )
    product_managers.permissions.add(*product_permissions)
    
    # Assign order-related permissions to OrderManagers
    order_permissions = Permission.objects.filter(
        content_type__in=[order_ct]
    )
    order_managers.permissions.add(*order_permissions)
    
    # Assign customer support permissions to CustomerSupportManagers
    support_permissions = Permission.objects.filter(
        content_type__in=[reclamacion_ct, newsletter_ct, profile_ct]
    )
    customer_support.permissions.add(*support_permissions)
    
    # Add view permissions for products to OrderManagers and CustomerSupportManagers
    view_product_perm = Permission.objects.get(codename='view_product', content_type=product_ct)
    order_managers.permissions.add(view_product_perm)
    customer_support.permissions.add(view_product_perm)
    
    return {
        'super_admins': super_admins,
        'product_managers': product_managers,
        'order_managers': order_managers,
        'customer_support': customer_support
    }

def assign_user_to_admin_group(user, group_name):
    """
    Assigns a user to a specific admin group and makes them staff.
    
    Args:
        user: The User instance to assign
        group_name: String name of the group ('SuperAdmins', 'ProductManagers', etc.)
        
    Returns:
        bool: True if successful, False if the group doesn't exist
    """
    try:
        group = Group.objects.get(name=group_name)
        user.groups.add(group)
        user.is_staff = True
        
        # Only SuperAdmins should be superusers
        if group_name == 'SuperAdmins':
            user.is_superuser = True
        
        user.save()
        return True
    except Group.DoesNotExist:
        return False

def remove_user_from_admin_groups(user):
    """
    Removes a user from all admin groups and revokes staff status if they're not in any admin group.
    
    Args:
        user: The User instance to remove from admin groups
    """
    admin_groups = ['SuperAdmins', 'ProductManagers', 'OrderManagers', 'CustomerSupportManagers']
    
    # Remove from all admin groups
    for group_name in admin_groups:
        try:
            group = Group.objects.get(name=group_name)
            user.groups.remove(group)
        except Group.DoesNotExist:
            pass
    
    # If user is not in any admin group, revoke staff and superuser status
    if not user.groups.filter(name__in=admin_groups).exists():
        user.is_staff = False
        user.is_superuser = False
        user.save()