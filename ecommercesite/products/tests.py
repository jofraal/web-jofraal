from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Product, Category, ProductVariant, ProductReview
from cart.models import Cart, CartItem # Import Cart for setup if needed

class ProductDetailViewTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            available=True
        )

    def test_product_detail_view(self):
        response = self.client.get(reverse('products:product_detail', kwargs={'id': self.product.id, 'slug': self.product.slug}))
        # Test using the CBV
        response = self.client.get(reverse('products:product_detail', kwargs={'id': self.product.id, 'slug': self.product.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
        self.assertTemplateUsed(response, 'products/product/detail.html')
        self.assertIsInstance(response.context['product'], Product)

class CartAddTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=100.00,
            available=True
        )
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_redirect_to_login_if_not_authenticated(self):
        response = self.client.post(reverse('cart:cart_add', args=[self.product.id]))
        self.assertRedirects(response, f"{reverse('users:login')}?next={self.product.get_absolute_url()}")

    def test_add_to_cart_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.post(reverse('cart:cart_add', args=[self.product.id]), data={'quantity': 1})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CartItem.objects.filter(cart__user=self.user, product=self.product).exists())

class ProductListViewTest(TestCase):
    def setUp(self):
        self.category1 = Category.objects.create(name='Category 1', slug='cat1')
        self.category2 = Category.objects.create(name='Category 2', slug='cat2')
        self.product1 = Product.objects.create(name='Product 1', slug='prod1', category=self.category1, price=50.00, available=True, gender='M')
        self.product2 = Product.objects.create(name='Product 2', slug='prod2', category=self.category2, price=150.00, available=True, gender='W')
        self.product3 = Product.objects.create(name='Product 3', slug='prod3', category=self.category1, price=25.00, available=True, gender='M')
        ProductVariant.objects.create(product=self.product1, color='Red', size='M')
        ProductVariant.objects.create(product=self.product2, color='Blue', size='L')

    def test_product_list_view_loads(self):
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product/list.html')
        self.assertContains(response, self.product1.name)
        self.assertContains(response, self.product2.name)
        self.assertEqual(len(response.context['products']), 3)

    def test_product_list_by_category(self):
        response = self.client.get(reverse('products:product_list_by_category', kwargs={'category_slug': self.category1.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/product/list.html')
        self.assertContains(response, self.product1.name)
        self.assertNotContains(response, self.product2.name)
        self.assertEqual(len(response.context['products']), 2)
        self.assertEqual(response.context['category'], self.category1)

    def test_product_list_filtering_gender(self):
        response = self.client.get(reverse('products:product_list'), {'gender': 'W'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product2.name)
        self.assertNotContains(response, self.product1.name)
        self.assertEqual(len(response.context['products']), 1)

    def test_product_list_filtering_price(self):
        response = self.client.get(reverse('products:product_list'), {'price': '0-50'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.name)
        self.assertContains(response, self.product3.name)
        self.assertNotContains(response, self.product2.name)
        self.assertEqual(len(response.context['products']), 2)

    def test_product_list_sorting(self):
        response = self.client.get(reverse('products:product_list'), {'sort_by': 'price_low'})
        self.assertEqual(response.status_code, 200)
        # Assuming default pagination shows all 3 products
        products_in_context = list(response.context['products'])
        self.assertEqual(products_in_context[0], self.product3)
        self.assertEqual(products_in_context[1], self.product1)
        self.assertEqual(products_in_context[2], self.product2)

class ProductReviewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.category = Category.objects.create(name='Test Category', slug='test-cat')
        self.product = Product.objects.create(name='Review Product', slug='review-prod', category=self.category, price=50.00)
        self.client = Client()
        self.client.login(username='testuser', password='password')
        self.submit_url = reverse('products:submit_review', args=[self.product.id])

    def test_submit_review_success(self):
        response = self.client.post(self.submit_url, {'rating': 4, 'comment': 'Good product!'})
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['success'])
        self.assertEqual(json_response['message'], 'Reseña enviada con éxito.')
        self.assertTrue(ProductReview.objects.filter(product=self.product, user=self.user, rating=4).exists())
        # Refresh product from DB to check updated average rating (if update_average_rating works)
        self.product.refresh_from_db()
        # self.assertEqual(self.product.average_rating, 4.0) # Uncomment if update_average_rating is implemented

    def test_submit_review_invalid_rating(self):
        response = self.client.post(self.submit_url, {'rating': 6, 'comment': 'Too high rating'})
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertIn('rating', json_response.get('errors', {}))

    def test_submit_review_missing_rating(self):
        response = self.client.post(self.submit_url, {'comment': 'No rating given'})
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertFalse(json_response['success'])
        self.assertIn('rating', json_response.get('errors', {}))

    def test_submit_review_not_logged_in(self):
        self.client.logout()
        response = self.client.post(self.submit_url, {'rating': 5})
        # Should redirect to login or return 403, depending on decorator
        # Assuming @login_required redirects
        self.assertEqual(response.status_code, 302)
        self.assertTrue(reverse('users:login') in response.url)
