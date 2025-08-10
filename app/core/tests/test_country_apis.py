from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Country

LIST_URL = reverse('country-list-create')

def get_detail_url(id):
    return reverse('country-update-destroy', kwargs={'id': id})

User = get_user_model()

class PublicTestCases(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_restrict_unauthenticated_user(self):
        response = self.client.post(LIST_URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTestCases(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            email='user@example.com',
            password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_new_country_successful(self):
        payload = {'name': 'bd'}
        response = self.client.post(LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('name', response.data)
        self.assertEqual(response.data['name'], payload['name'])
        self.assertNotIn('user', response.data)

    def test_create_duplicate_country_unsuccessful(self):
        payload = {'name': 'bd'}
        self.client.post(LIST_URL, payload)
        response = self.client.post(LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_empty_country_unsuccessful(self):
        payload = {'name': ''}
        response = self.client.post(LIST_URL, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_successful(self):
        response1 = self.client.post(LIST_URL, {'name': 'bd'})
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response1.data)
        country_id = response1.data['id']
        payload = {'name': 'malaysia'}
        response2 = self.client.patch(get_detail_url(id=country_id), payload)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertIn('name', response2.data)
        self.assertEqual(response2.data['name'], payload['name'])

    def test_get_countries_filtered_by_auth_user(self):
        self.client.post(LIST_URL, {'name': 'bd'})
        user = User.objects.create_user(
            email='new@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        payload = {'name': 'pak'}
        self.client.post(LIST_URL, payload)

        countries = Country.objects.filter(user=user)
        self.assertEqual(len(countries), 1)
        all_countries = Country.objects.all()
        self.assertEqual(len(all_countries), 2)
        self.assertEqual(countries[0].name, payload['name'])

    def test_delete_successful(self):
        response = self.client.post(LIST_URL, {'name': 'bd'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        countries = Country.objects.all()
        self.assertEqual(len(countries), 1)
        country_id = response.data['id']
        response = self.client.delete(get_detail_url(id=country_id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        countries = Country.objects.all()
        self.assertEqual(len(countries), 0)

    def test_delete_other_users_country_unsuccessful(self):
        response = self.client.post(LIST_URL, {'name': 'bd'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        country_id = response.data['id']
        user = User.objects.create_user(
            email='new@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        response = self.client.delete(get_detail_url(id=country_id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)