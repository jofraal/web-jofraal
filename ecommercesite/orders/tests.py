from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from cart.models import Cart, CartItem
from products.models import Product, Category, ProductVariant
from .models import Order
from .locations import get_departments, get_provinces, get_districts
import json

class OrderViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password', email='test@example.com', first_name='Test', last_name='User')
        self.category = Category.objects.create(name='Test Category', slug='test-cat')
        self.product = Product.objects.create(name='Test Product', slug='test-prod', category=self.category, price=50.00)
        self.variant = ProductVariant.objects.create(product=self.product, color='Red', size='M', stock=10)
        self.cart = Cart.objects.create(user=self.user)
        self.cart_item = CartItem.objects.create(cart=self.cart, product=self.product, variant=self.variant, quantity=1, selected=True)

    def test_checkout_view_get_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('orders:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/checkout.html')
        self.assertIn('identification_form', response.context)
        self.assertIn('shipping_form', response.context)
        self.assertIn('cart', response.context)
        self.assertIn('selected_items', response.context)
        self.assertEqual(response.context['active_step'], 'identification') # Default step

    def test_checkout_view_get_unauthenticated(self):
        # Assuming checkout requires login or handles anonymous users differently
        # If it redirects anonymous users, test that
        response = self.client.get(reverse('orders:checkout'))
        # Depending on implementation, it might redirect to login or show cart
        # Let's assume it redirects to cart if no items or shows cart page
        # If it requires login, it should redirect to login page
        # Based on views.py, it gets/creates cart, so it likely proceeds
        self.assertEqual(response.status_code, 200) # Or 302 if login required
        self.assertTemplateUsed(response, 'orders/checkout.html') # Or login template

    def test_checkout_view_post_identification_step_valid(self):
        self.client.login(username='testuser', password='password')
        data = {
            'step': 'identification',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '987654321',
            'terms_accepted': 'on',
            # Add other required fields for OrderIdentificationForm if any
        }
        response = self.client.post(reverse('orders:checkout'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/checkout.html')
        self.assertEqual(response.context['active_step'], 'shipping')
        self.assertEqual(self.client.session.get('identification_data')['email'], 'test@example.com')

    def test_checkout_view_post_identification_step_invalid(self):
        self.client.login(username='testuser', password='password')
        data = {
            'step': 'identification',
            'first_name': '', # Missing required field
            'last_name': 'User',
            'email': 'invalid-email',
            'phone': '987654321',
            'terms_accepted': 'on',
        }
        response = self.client.post(reverse('orders:checkout'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders/checkout.html')
        self.assertEqual(response.context['active_step'], 'identification') # Stays on identification step
        self.assertTrue(response.context['identification_form'].errors)

    # Test for shipping step requires mocking MercadoPago or testing create_payment directly
    # Add basic test for create_payment failure without items
    def test_create_payment_no_selected_items(self):
        self.client.login(username='testuser', password='password')
        # Deselect item
        self.cart_item.selected = False
        self.cart_item.save()
        response = self.client.post(reverse('orders:create_payment'), {'cardholderEmail': 'test@example.com', 'transaction_amount': '50.00'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(response.json()['error'], 'No hay productos seleccionados')

class LocationAPITest(TestCase):
    def test_get_departments_api(self):
        response = self.client.get(reverse('orders:get_departments_api'))
        self.assertEqual(response.status_code, 200)
        departments = json.loads(response.content)
        self.assertIsInstance(departments, list)
        self.assertTrue(len(departments) > 0) # Assuming Peru has departments
        self.assertIn('Lima', departments) # Example check

    def test_get_provinces_api(self):
        department = 'Lima' # Example department
        response = self.client.get(reverse('orders:get_provinces_api'), {'department': department})
        self.assertEqual(response.status_code, 200)
        provinces = json.loads(response.content)
        self.assertIsInstance(provinces, list)
        self.assertTrue(len(provinces) > 0)
        self.assertIn('Lima', provinces) # Example check

    def test_get_provinces_api_invalid_department(self):
        response = self.client.get(reverse('orders:get_provinces_api'), {'department': 'InvalidDept'})
        self.assertEqual(response.status_code, 200) # API returns empty list for invalid
        provinces = json.loads(response.content)
        self.assertEqual(provinces, [])

    def test_get_districts_api(self):
        department = 'Lima'
        province = 'Lima' # Example province
        response = self.client.get(reverse('orders:get_districts_api'), {'department': department, 'province': province})
        self.assertEqual(response.status_code, 200)
        districts = json.loads(response.content)
        self.assertIsInstance(districts, list)
        self.assertTrue(len(districts) > 0)
        self.assertIn('Miraflores', districts) # Example check

    def test_get_districts_api_missing_param(self):
        response = self.client.get(reverse('orders:get_districts_api'), {'department': 'Lima'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
