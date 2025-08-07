from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Tag
from django.contrib.auth import get_user_model
from django.urls import reverse

URL = reverse('tags-list-create')

User = get_user_model()


class PrivateTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_tag_successful(self):
        payload = {'name': 'hifi'}
        response = self.client.post(URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'), payload['name'])

    def test_create_tag_unsuccessful(self):
        payload = {'name': ''}
        response = self.client.post(URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_tags_filtered_by_authenticated_user(self):
        payload1 = {'name': 'hifi'}
        payload2 = {'name': 'important'}
        self.client.post(URL, payload1)
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass12345'
        )
        self.client.force_authenticate(user=user2)
        response2 = self.client.post(URL, payload2)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        all_tags = Tag.objects.all()
        tags = all_tags.filter(user=user2)
        self.assertEqual(len(tags), 1)
        self.assertEqual(len(all_tags), 2)
        self.assertEqual(str(tags[0]), payload2['name'])
