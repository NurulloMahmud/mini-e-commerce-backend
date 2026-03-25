from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from products.models import Product
from .models import Cart


def make_product(name='Product', price='20.00', category='General'):
    return Product.objects.create(name=name, price=price, category=category)


class CartTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/cart/'
        self.user = User.objects.create_user(phone='+998901111111', password='pass123', fullname='User')
        self.other_user = User.objects.create_user(phone='+998903333333', password='pass123', fullname='Other')
        self.product = make_product('Phone', '299.99')
        self._auth(self.user)

    def _auth(self, user):
        res = self.client.post('/api/auth/login/', {'phone': user.phone, 'password': 'pass123'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    # --- GET /api/cart/ ---

    def test_get_empty_cart(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['items'], [])
        self.assertEqual(str(res.data['total']), '0')

    def test_get_cart_requires_auth(self):
        self.client.credentials()
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- POST /api/cart/ ---

    def test_add_item_to_cart(self):
        res = self.client.post(self.url, {'product_id': self.product.id, 'quantity': 2})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['quantity'], 2)
        self.assertEqual(res.data['product']['name'], 'Phone')

    def test_add_same_item_increments_quantity(self):
        self.client.post(self.url, {'product_id': self.product.id, 'quantity': 1})
        self.client.post(self.url, {'product_id': self.product.id, 'quantity': 3})
        cart = self.client.get(self.url)
        self.assertEqual(len(cart.data['items']), 1)
        self.assertEqual(cart.data['items'][0]['quantity'], 4)

    def test_add_nonexistent_product(self):
        res = self.client.post(self.url, {'product_id': 9999, 'quantity': 1})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_without_product_id(self):
        res = self.client.post(self.url, {'quantity': 1})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cart_total_calculated_correctly(self):
        p2 = make_product('Laptop', '500.00')
        self.client.post(self.url, {'product_id': self.product.id, 'quantity': 2})  # 299.99 * 2 = 599.98
        self.client.post(self.url, {'product_id': p2.id, 'quantity': 1})            # 500.00 * 1 = 500.00
        res = self.client.get(self.url)
        self.assertEqual(float(res.data['total']), 1099.98)

    def test_users_cannot_see_each_others_carts(self):
        self.client.post(self.url, {'product_id': self.product.id, 'quantity': 1})
        self._auth(self.other_user)
        res = self.client.get(self.url)
        self.assertEqual(res.data['items'], [])

    # --- PATCH /api/cart/<id>/ ---

    def test_update_cart_item_quantity(self):
        add_res = self.client.post(self.url, {'product_id': self.product.id, 'quantity': 1})
        item_id = add_res.data['id']
        res = self.client.patch(f'{self.url}{item_id}/', {'quantity': 5})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['quantity'], 5)

    def test_update_quantity_to_zero_invalid(self):
        add_res = self.client.post(self.url, {'product_id': self.product.id, 'quantity': 1})
        item_id = add_res.data['id']
        res = self.client.patch(f'{self.url}{item_id}/', {'quantity': 0})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_update_other_users_cart_item(self):
        add_res = self.client.post(self.url, {'product_id': self.product.id, 'quantity': 1})
        item_id = add_res.data['id']
        self._auth(self.other_user)
        res = self.client.patch(f'{self.url}{item_id}/', {'quantity': 99})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # --- DELETE /api/cart/<id>/ ---

    def test_delete_cart_item(self):
        add_res = self.client.post(self.url, {'product_id': self.product.id, 'quantity': 1})
        item_id = add_res.data['id']
        res = self.client.delete(f'{self.url}{item_id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Cart.objects.filter(id=item_id).count(), 0)

    def test_cannot_delete_other_users_cart_item(self):
        add_res = self.client.post(self.url, {'product_id': self.product.id, 'quantity': 1})
        item_id = add_res.data['id']
        self._auth(self.other_user)
        res = self.client.delete(f'{self.url}{item_id}/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
