from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

User = get_user_model()
URL_ME = reverse('me')
URL_Register = reverse('register')

class PublicTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_new_user_successful(self):
        email = 'test@example.com'
        payload = {
            'email': email,
            'password': 'testpass123'
        }
        response = self.client.post(URL_Register, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'], email)
        self.assertNotIn('password', response.data)

    def test_register_new_user_short_password(self):
        email = 'test@example.com'
        payload = {
            'email': email,
            'password': '123'
        }
        response = self.client.post(URL_Register, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_new_user_invalid_email(self):
        email = 'test.com'
        payload = {
            'email': email,
            'password': 'testpass123'
        }
        response = self.client.post(URL_Register, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PrivateTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = 'test@example.com'
        self.password = 'testpass123'
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password
        )

    def test_get_user_detail_successful(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(URL_ME)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email', response.data)
        self.assertNotIn('password', response.data)
        self.assertEqual(response.data['email'], self.email)

    def test_get_user_detail_unsuccessful(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(URL_ME)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_detail_not_allowed(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(URL_ME, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_detail_successful(self):
        payload = {
            'email': 'new@example.com',
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(URL_ME, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload['email'])
