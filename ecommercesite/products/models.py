from django.db import models
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.models import User  # Add this import

class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_products(self):
        """Devuelve todos los productos asociados a esta categoría."""
        return self.products.all()


class Brand(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)

    def __str__(self):
        return self.name

    def get_products(self):
        """Devuelve todos los productos asociados a esta marca."""
        return self.products.all()


class Product(models.Model):
    GENDER_CHOICES = [('M', 'Men'), ('W', 'Women'), ('U', 'Unisex')]

    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(upload_to='products', blank=True, null=True)
    collection_featured = models.BooleanField(default=False)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='U')
    free_shipping = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, default=None)  # Keep this definition

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'id': self.id, 'slug': self.slug})

    def calculate_discount_percentage(self):
        """Calcula el mayor porcentaje de descuento entre las variantes."""
        variants = self.variants.all()
        if not variants:
            return 0
        # Crear una lista de descuentos de variantes con descuento activo
        discounts = [variant.discount_percentage for variant in variants if variant.has_discount()]
        # Verificar si hay descuentos antes de usar max()
        if not discounts:
            return 0
        return max(discounts)

    def calculate_discounted_price(self):
        """Calcula el precio con descuento si aplica."""
        discount_percentage = self.calculate_discount_percentage()
        if discount_percentage > 0:
            discount_factor = Decimal(str(1 - (discount_percentage / 100)))
            discounted = self.price * discount_factor
            return discounted.quantize(Decimal('0.01'))
        return self.price

    def get_image_url(self):
        """Returns the image URL or a default image if none exists."""
        if self.image and hasattr(self.image, 'url'):
            return self.image.url  # Points to MEDIA_URL + file path
        return f"/static/images/default-product.jpg"  # Default image in static files

    @property
    def original_price(self):
        return self.price

    @property
    def discounted_price(self):
        return self.calculate_discounted_price()

    @property
    def discount_percentage(self):
        # Retornar el porcentaje de descuento sin decimales
        return int(self.calculate_discount_percentage())

    def user_has_purchased(self, user):
        # Verificar si el usuario está autenticado
        if not user or not user.is_authenticated:
            return False
            
        # Importar aquí para evitar importaciones circulares
        from orders.models import OrderItem
        
        # Verificar si el usuario ha comprado este producto
        try:
            return OrderItem.objects.filter(
                product=self,
                order__user=user,
                order__paid=True
            ).exists()
        except Exception:
            # Si hay algún error, asumimos que no ha comprado
            return False

    @property
    def average_rating(self):
        """Returns the average rating or 0 if no reviews exist"""
        if self.rating is None:
            return 0
        return float(self.rating)

    def update_rating(self):
        """Updates the product rating based on reviews"""
        reviews = self.reviews.all()
        if reviews:
            avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.rating = round(avg_rating, 2) if avg_rating else 0
        else:
            self.rating = 0
        self.save(update_fields=['rating'])


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color = models.CharField(max_length=50, default='gray')
    size = models.CharField(max_length=10, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Porcentaje de descuento (0-100)')
    discount_start_date = models.DateTimeField(blank=True, null=True, help_text='Fecha de inicio de la promoción')
    discount_end_date = models.DateTimeField(blank=True, null=True, help_text='Fecha de fin de la promoción')

    def has_discount(self):
        now = timezone.now()
        return self.discount_percentage > 0 and (not self.discount_start_date or self.discount_start_date <= now) and (not self.discount_end_date or self.discount_end_date >= now)

    def get_price(self):
        if self.has_discount():
            discount_factor = Decimal(1 - (self.discount_percentage / 100))
            return (self.product.price * discount_factor).quantize(Decimal('0.01'))
        return self.product.price

    def clean(self):
        if self.discount_percentage < 0 or self.discount_percentage > 100:
            raise ValidationError('El porcentaje de descuento debe estar entre 0 y 100.')
        if self.stock < 0:
            raise ValidationError('El stock no puede ser negativo.')

    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size or 'Talla única'}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # Rating out of 5
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # Prevent duplicate reviews by the same user

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()