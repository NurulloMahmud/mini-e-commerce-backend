from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'

    # --- Register ---

    def test_register_success(self):
        res = self.client.post(self.register_url, {
            'fullname': 'Ali Valiyev',
            'phone': '+998901234567',
            'password': 'secret123',
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.data['user']['phone'], '+998901234567')
        self.assertIn('is_staff', res.data['user'])
        self.assertFalse(res.data['user']['is_staff'])

    def test_register_duplicate_phone(self):
        User.objects.create_user(phone='+998901234567', password='pass', fullname='Ali')
        res = self.client.post(self.register_url, {
            'fullname': 'Bek',
            'phone': '+998901234567',
            'password': 'secret123',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        res = self.client.post(self.register_url, {'phone': '+998901234567'})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        res = self.client.post(self.register_url, {
            'fullname': 'Ali',
            'phone': '+998901234567',
            'password': '123',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Login ---

    def test_login_success(self):
        User.objects.create_user(phone='+998901234567', password='secret123', fullname='Ali')
        res = self.client.post(self.login_url, {
            'phone': '+998901234567',
            'password': 'secret123',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('is_staff', res.data['user'])

    def test_login_wrong_password(self):
        User.objects.create_user(phone='+998901234567', password='secret123', fullname='Ali')
        res = self.client.post(self.login_url, {
            'phone': '+998901234567',
            'password': 'wrongpass',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        res = self.client.post(self.login_url, {
            'phone': '+998000000000',
            'password': 'anything',
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_user_is_staff_true(self):
        User.objects.create_superuser(phone='+998999999999', password='adminpass', fullname='Admin')
        res = self.client.post(self.login_url, {
            'phone': '+998999999999',
            'password': 'adminpass',
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['user']['is_staff'])
