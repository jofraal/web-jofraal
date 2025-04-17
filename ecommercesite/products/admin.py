from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Category, Product, ProductVariant, Brand, ProductReview

class ProductVariantForm(forms.ModelForm):
    PREDEFINED_SIZES = ['S', 'M', 'L', 'XL', 'XXL']  # Ensure consistency with predefined sizes

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['size'].widget = forms.Select(choices=[(size, size) for size in self.PREDEFINED_SIZES] + [('', '---------')])

    class Meta:
        model = ProductVariant
        fields = '__all__'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    form = ProductVariantForm
    extra = 1
    fields = ('color', 'size', 'stock', 'discount_percentage', 'discount_start_date', 'discount_end_date')
    readonly_fields = ('get_price',)
    show_change_link = True

    def get_price(self, obj):
        return obj.get_price()
    get_price.short_description = "Precio con descuento"

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'available', 'total_stock', 'created', 'updated', 'image_preview', 'view_on_site_link')
    list_filter = ('available', 'category', 'brand', 'created', 'updated', 'price')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    actions = ['mark_as_available', 'mark_as_unavailable', 'generate_variants']
    inlines = [ProductVariantInline]

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: auto;" />', obj.image.url)
        return "Sin imagen"
    image_preview.short_description = "Vista previa"

    def view_on_site_link(self, obj):
        """Genera un enlace para ver el producto en el sitio."""
        if obj.id and obj.slug:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">Ver en el sitio</a>', url)
        return "No disponible"
    view_on_site_link.short_description = "Ver en el sitio"

    def mark_as_available(self, request, queryset):
        updated = queryset.update(available=True)
        self.message_user(request, f"{updated} productos marcados como disponibles.")
    mark_as_available.short_description = "Marcar como disponibles"

    def mark_as_unavailable(self, request, queryset):
        updated = queryset.update(available=False)
        self.message_user(request, f"{updated} productos marcados como no disponibles.")
    mark_as_unavailable.short_description = "Marcar como no disponibles"

    def total_stock(self, obj):
        return sum(variant.stock for variant in obj.variants.all())
    total_stock.short_description = "Stock total"

    def generate_variants(self, request, queryset):
        colors = ['Red', 'Blue', 'Green']
        sizes = ['S', 'M', 'L']
        for product in queryset:
            for color in colors:
                for size in sizes:
                    ProductVariant.objects.get_or_create(product=product, color=color, size=size)
        self.message_user(request, "Variantes generadas exitosamente.")
    generate_variants.short_description = "Generar variantes (colores y tallas)"

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'color', 'size', 'stock', 'discount_percentage')
    list_filter = ('color', 'size', 'discount_percentage', 'stock')
    search_fields = ('product__name', 'color', 'size')

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')

