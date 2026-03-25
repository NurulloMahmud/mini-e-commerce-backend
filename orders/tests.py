from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from products.models import Product
from cart.models import Cart
from .models import Order


def make_product(name='Product', price='50.00', category='General'):
    return Product.objects.create(name=name, price=price, category=category)


class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.order_url = '/api/orders/'
        self.cart_url = '/api/cart/'
        self.user = User.objects.create_user(phone='+998901111111', password='pass123', fullname='User')
        self.other_user = User.objects.create_user(phone='+998903333333', password='pass123', fullname='Other')
        self.product = make_product('Shirt', '25.00')
        self._auth(self.user)

    def _auth(self, user):
        res = self.client.post('/api/auth/login/', {'phone': user.phone, 'password': 'pass123'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    def _fill_cart(self, qty=2):
        self.client.post(self.cart_url, {'product_id': self.product.id, 'quantity': qty})

    # --- POST /api/orders/ ---

    def test_place_order_success(self):
        self._fill_cart(qty=3)
        res = self.client.post(self.order_url)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(float(res.data['total']), 75.00)  # 25.00 * 3
        self.assertEqual(res.data['status'], 'pending')
        self.assertEqual(len(res.data['items']), 1)

    def test_order_items_capture_product_details(self):
        self._fill_cart(qty=2)
        res = self.client.post(self.order_url)
        item = res.data['items'][0]
        self.assertEqual(item['product_name'], 'Shirt')
        self.assertEqual(float(item['price']), 25.00)
        self.assertEqual(item['quantity'], 2)
        self.assertEqual(float(item['subtotal']), 50.00)

    def test_cart_is_cleared_after_order(self):
        self._fill_cart()
        self.client.post(self.order_url)
        cart_res = self.client.get(self.cart_url)
        self.assertEqual(cart_res.data['items'], [])

    def test_place_order_with_empty_cart(self):
        res = self.client.post(self.order_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_place_order_requires_auth(self):
        self.client.credentials()
        res = self.client.post(self.order_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_total_with_multiple_products(self):
        p2 = make_product('Pants', '40.00')
        self.client.post(self.cart_url, {'product_id': self.product.id, 'quantity': 2})  # 50
        self.client.post(self.cart_url, {'product_id': p2.id, 'quantity': 3})             # 120
        res = self.client.post(self.order_url)
        self.assertEqual(float(res.data['total']), 170.00)

    # --- GET /api/orders/ ---

    def test_list_orders(self):
        self._fill_cart()
        self.client.post(self.order_url)
        res = self.client.get(self.order_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_users_only_see_their_own_orders(self):
        self._fill_cart()
        self.client.post(self.order_url)  # user places order
        self._auth(self.other_user)
        res = self.client.get(self.order_url)
        self.assertEqual(res.data, [])

    def test_get_order_detail(self):
        self._fill_cart()
        order_res = self.client.post(self.order_url)
        order_id = order_res.data['id']
        res = self.client.get(f'{self.order_url}{order_id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], order_id)

    def test_cannot_access_other_users_order(self):
        self._fill_cart()
        order_res = self.client.post(self.order_url)
        order_id = order_res.data['id']
        self._auth(self.other_user)
        res = self.client.get(f'{self.order_url}{order_id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_multiple_orders_accumulate(self):
        p2 = make_product('Hat', '15.00')
        self._fill_cart()
        self.client.post(self.order_url)
        self.client.post(self.cart_url, {'product_id': p2.id, 'quantity': 1})
        self.client.post(self.order_url)
        res = self.client.get(self.order_url)
        self.assertEqual(len(res.data), 2)
