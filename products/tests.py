from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import Product


def make_product(**kwargs):
    defaults = {'name': 'Test Product', 'price': '10.00', 'category': 'Electronics'}
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


class ProductTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/products/'
        self.user = User.objects.create_user(phone='+998901111111', password='pass123', fullname='User')
        self.admin = User.objects.create_superuser(phone='+998902222222', password='pass123', fullname='Admin')

    def auth(self, user):
        res = self.client.post('/api/auth/login/', {'phone': user.phone, 'password': 'pass123'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {res.data["access"]}')

    # --- GET /api/products/ (public) ---

    def test_list_products_public(self):
        make_product(name='Phone')
        make_product(name='Laptop', category='Computers')
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_list_products_search(self):
        make_product(name='iPhone 15')
        make_product(name='Samsung TV')
        res = self.client.get(self.url + '?search=iphone')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], 'iPhone 15')

    def test_list_products_filter_by_category(self):
        make_product(name='Phone', category='Mobile')
        make_product(name='TV', category='Electronics')
        res = self.client.get(self.url + '?category=Mobile')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    # --- POST /api/products/ (admin only) ---

    def test_create_product_as_admin(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {
            'name': 'Headphones',
            'price': '49.99',
            'category': 'Audio',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['name'], 'Headphones')

    def test_create_product_as_regular_user_forbidden(self):
        self.auth(self.user)
        res = self.client.post(self.url, {'name': 'X', 'price': '10.00', 'category': 'Y'})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_product_unauthenticated_forbidden(self):
        res = self.client.post(self.url, {'name': 'X', 'price': '10.00', 'category': 'Y'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_product_invalid_price(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {'name': 'Bad', 'price': '-5.00', 'category': 'X'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_zero_price(self):
        self.auth(self.admin)
        res = self.client.post(self.url, {'name': 'Free', 'price': '0.00', 'category': 'X'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # --- DELETE /api/products/<id>/ ---

    def test_delete_product_as_admin(self):
        p = make_product()
        self.auth(self.admin)
        res = self.client.delete(f'{self.url}{p.id}/')
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_product_as_regular_user_forbidden(self):
        p = make_product()
        self.auth(self.user)
        res = self.client.delete(f'{self.url}{p.id}/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_single_product(self):
        p = make_product(name='Watch')
        res = self.client.get(f'{self.url}{p.id}/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['name'], 'Watch')

    def test_get_nonexistent_product(self):
        res = self.client.get(f'{self.url}9999/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
