from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


class CustomAdminSite(AdminSite):
    site_header = "Panel de Administración"
    site_title = "Admin - Ecommerce"
    index_title = "Bienvenido al Panel de Administración"

    MODEL_GROUPS = {
        'Catálogo': {
            'icon': '📦',
            'models': {'Product', 'ProductVariant', 'Category', 'Brand', 'ProductReview'},
        },
        'Ventas': {
            'icon': '💰',
            'models': {'Order', 'OrderItem', 'Cart', 'CartItem', 'Coupon'},
        },
        'Clientes': {
            'icon': '👥',
            'models': {'User', 'Reclamacion', 'NewsletterSubscriber'},
        },
    }

    def get_admin_stats(self):
        from orders.models import Order
        from products.models import Product, ProductVariant
        from django.contrib.auth.models import User

        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        total_revenue = Order.objects.filter(paid=True).aggregate(
            total=Sum('total')
        )['total'] or 0

        revenue_30d = Order.objects.filter(
            paid=True, created_at__gte=thirty_days_ago
        ).aggregate(total=Sum('total'))['total'] or 0

        return {
            'total_revenue': total_revenue,
            'revenue_30d': revenue_30d,
            'pending_orders': Order.objects.filter(paid=False).count(),
            'total_orders': Order.objects.count(),
            'total_products': Product.objects.count(),
            'total_variants': ProductVariant.objects.count(),
            'total_users': User.objects.count(),
            'new_users_30d': User.objects.filter(
                date_joined__gte=thirty_days_ago
            ).count(),
            'low_stock': ProductVariant.objects.filter(
                stock__lte=5, stock__gt=0
            ).count(),
            'out_of_stock': ProductVariant.objects.filter(stock=0).count(),
            'recent_orders': Order.objects.select_related('user').order_by(
                '-created_at'
            )[:5],
        }

    def each_context(self, request):
        context = super().each_context(request)
        context['admin_stats'] = self.get_admin_stats()
        return context

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        grouped = {}
        ungrouped = []

        for app in app_list:
            for model in app.get('models', []):
                model_name = model.get('object_name', '')
                assigned = False
                for group_name, group_info in self.MODEL_GROUPS.items():
                    if model_name in group_info['models']:
                        if group_name not in grouped:
                            grouped[group_name] = {
                                'name': f"{group_info['icon']} {group_name}",
                                'app_label': group_name.lower(),
                                'app_url': '#',
                                'has_module_perms': True,
                                'models': [],
                            }
                        if model not in grouped[group_name]['models']:
                            grouped[group_name]['models'].append(model)
                        assigned = True
                        break
                if not assigned:
                    ungrouped.append(model)

        new_app_list = list(grouped.values())
        if ungrouped:
            new_app_list.append({
                'name': 'Otros',
                'app_label': 'otros',
                'app_url': '#',
                'has_module_perms': True,
                'models': ungrouped,
            })

        for app in app_list:
            if app.get('app_label') == 'auth':
                new_app_list.append(app)
                break

        return new_app_list


custom_admin_site = CustomAdminSite(name='custom_admin')

# Compartir el registro de modelos con el admin.site estándar
# (todos los modelos ya están registrados vía admin.autodiscover)
custom_admin_site._registry = admin.site._registry
