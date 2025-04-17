from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView
from .models import Category, Product, ProductVariant, ProductReview
from .forms import ProductReviewForm # Import the form

# Helper function for filtering products
def _filter_products(request, queryset):
    """Applies filters from request GET parameters to a queryset."""
    selected_genders = request.GET.getlist('gender')
    if selected_genders:
        queryset = queryset.filter(gender__in=selected_genders)

    selected_colors = request.GET.getlist('color')
    if selected_colors:
        queryset = queryset.filter(variants__color__in=selected_colors).distinct()

    selected_sizes = request.GET.getlist('size')
    if selected_sizes:
        queryset = queryset.filter(variants__size__in=selected_sizes).distinct()

    selected_prices = request.GET.getlist('price')
    if selected_prices:
        price_filters = Q()
        for price_range in selected_prices:
            try:
                min_price, max_price = map(float, price_range.split('-'))
                price_filters |= Q(price__gte=min_price, price__lte=max_price)
            except ValueError:
                continue # Ignore invalid price ranges
        queryset = queryset.filter(price_filters)

    sort_by = request.GET.get('sort_by', '')
    if sort_by == 'price_low':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_high':
        queryset = queryset.order_by('-price')
    elif sort_by == 'newest':
        queryset = queryset.order_by('-created')
    else: # Default sort
        queryset = queryset.order_by('-created')

    return queryset

class ProductListView(ListView):
    model = Product
    template_name = 'products/product/list.html'
    context_object_name = 'products'
    paginate_by = 12 # Example: Add pagination

    def get_queryset(self):
        queryset = Product.objects.filter(available=True).select_related('category', 'brand').prefetch_related('variants')
        self.category = None
        category_slug = self.kwargs.get('category_slug')
        selected_categories_get = self.request.GET.getlist('category')

        if category_slug:
            self.category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=self.category)
        elif selected_categories_get:
            queryset = queryset.filter(category__slug__in=selected_categories_get).distinct()
            if len(selected_categories_get) == 1:
                 try:
                     self.category = Category.objects.get(slug=selected_categories_get[0])
                 except Category.DoesNotExist:
                     pass # Keep self.category as None

        # Apply common filters using the helper function
        queryset = _filter_products(self.request, queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_variants = ProductVariant.objects.values('color', 'size').distinct()

        context['category'] = self.category
        context['categories'] = Category.objects.all().prefetch_related('products')
        context['price_ranges'] = [
            {"value": "0-50", "label": "Hasta S/ 50"},
            {"value": "50-100", "label": "S/ 50 - S/ 100"},
            {"value": "100-250", "label": "S/ 100 - S/ 250"},
            {"value": "250-500", "label": "S/ 250 - S/ 500"}
        ]
        context['genders'] = [
            {"value": "M", "label": "Hombre"},
            {"value": "W", "label": "Mujer"},
            {"value": "U", "label": "Unisex"}
        ]
        context['colors'] = sorted([variant['color'] for variant in all_variants if variant['color']])
        context['sizes'] = sorted([variant['size'] for variant in all_variants if variant['size']])

        # Pass selected filters to context for template rendering
        context['selected_categories'] = self.request.GET.getlist('category') if not self.kwargs.get('category_slug') else [self.kwargs.get('category_slug')]
        context['selected_genders'] = self.request.GET.getlist('gender')
        context['selected_colors'] = self.request.GET.getlist('color')
        context['selected_sizes'] = self.request.GET.getlist('size')
        context['selected_prices'] = self.request.GET.getlist('price')
        context['sort_by'] = self.request.GET.get('sort_by', '')

        return context

def product_list_ajax(request):
    products = Product.objects.filter(available=True).select_related('category').prefetch_related('variants')

    category_slug = request.GET.get('category_slug')
    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            products = products.filter(category=category)
        except Category.DoesNotExist:
            # If category doesn't exist, maybe return empty or all products based on requirements
            # Here, we continue filtering the base queryset
            pass 

    # Apply common filters using the helper function
    products = _filter_products(request, products)

    product_data = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'price': float(p.price),
        'discounted_price': float(p.discounted_price),
        'original_price': float(p.price),
        'discount_percentage': p.discount_percentage,
        'image': p.image.url if p.image else None,
        'free_shipping': p.free_shipping,
        'brand': p.brand if hasattr(p, 'brand') else 'Made in Perù',
    } for p in products]

    return JsonResponse({'products': product_data})

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product/detail.html'
    context_object_name = 'product'
    # Use slug and id for lookup as before
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'id'

    def get_queryset(self):
        # Ensure we only show available products
        return super().get_queryset().filter(available=True).prefetch_related('variants', 'reviews')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()

        # Get distinct colors for the product, sorted alphabetically
        variant_colors = sorted(list(product.variants.values_list('color', flat=True).distinct()))
        context['variant_colors'] = variant_colors

        # Get related products
        related_products = Product.objects.filter(
            category=product.category, available=True
        ).exclude(id=product.id).select_related('category').prefetch_related('variants', 'reviews').order_by('?')[:4]

        # Ensure related products have a rating value (can be improved with annotation)
        for related in related_products:
            if related.rating is None:
                related.rating = 0 # Or handle appropriately in template

        context['related_products'] = related_products
        context['variants'] = product.variants.all() # Pass variants explicitly if needed

        return context

def coleccion(request):
    featured_products = Product.objects.filter(collection_featured=True)
    return render(request, 'products/coleccion.html', {'products': featured_products})

def product_list_by_gender(request, gender):
    if gender.upper() not in ['M', 'W', 'U']:
        return render(request, 'core/404.html', status=404)
    products = Product.objects.filter(available=True, gender=gender.upper()).select_related('category').prefetch_related('variants')
    return render(request, 'products/product/list_by_gender.html', {
        'products': products,
        'gender': gender,
    })

# Use Django Form for review submission validation
@login_required
@require_POST
def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user
    form = ProductReviewForm(request.POST)

    if form.is_valid():
        # Create or update the review
        review, created = ProductReview.objects.update_or_create(
            product=product,
            user=user,
            defaults=form.cleaned_data
        )

        # Recalculate average rating (consider moving this logic to model save method or signal)
        # Ensure the method exists and works correctly
        try:
            product.update_average_rating()
        except AttributeError:
            # Handle case where method doesn't exist or log a warning
            logger.warning(f"Product model does not have 'update_average_rating' method.")
            # Optionally, calculate manually if needed, though model method is preferred
            pass

        return JsonResponse({
            'success': True,
            'message': 'Reseña enviada con éxito.',
            'rating': review.rating,
            'comment': review.comment,
            'average_rating': product.average_rating # Use the potentially updated average rating
        })
    else:
        # Return validation errors
        # Format errors for JSON response
        errors = {field: error[0] for field, error in form.errors.items()}
        return JsonResponse({'success': False, 'message': 'Error en la validación.', 'errors': errors}, status=400)