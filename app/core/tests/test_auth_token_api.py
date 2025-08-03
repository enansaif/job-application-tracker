from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

User = get_user_model()
Url = reverse('token')

class PublicTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.email = 'test@example.com'
        self.password = 'testpass123'
        User.objects.create_user(
            email=self.email,
            password=self.password
        )

    def test_generate_token_successful(self):
        payload = {
            'email': self.email,
            'password':self.password
        }
        response = self.client.post(Url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_generate_token_unsuccessful(self):
        payload = {
            'email': self.email,
            'password': 'wrongpass123'
        }
        response = self.client.post(Url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)