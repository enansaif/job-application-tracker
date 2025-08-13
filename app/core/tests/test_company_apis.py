from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import Company, Tag

COUNTRY_LIST_URL = reverse('country-list-create')
COMPANY_LIST_URL = reverse('company-list-create')
User = get_user_model()

class PublicTestCase(TestCase):
    """Test unauthenticated company-list-create requests"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Unauthenticated users should not be able to access company list/create"""
        res = self.client.get(COMPANY_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTestCase(TestCase):
    """Test authenticated company-list-create requests"""
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        # create a country
        response = self.client.post(COUNTRY_LIST_URL, {'name': 'bd'})
        self.country_id = response.data['id']

    def test_create_company_successful(self):
        payload = {
            "name": "dummy-company",
            "country": self.country_id,
            "link": "https://dummy-company.com",
            "tags": ["mnc", "se-ii"]
        }
        res = self.client.post(COMPANY_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        company = Company.objects.get(id=res.data['id'])
        self.assertEqual(company.name, payload['name'])
        self.assertEqual(company.country.id, self.country_id)
        self.assertEqual(set(t.name for t in company.tags.all()), set(payload['tags']))

    def test_create_without_country_or_tags(self):
        payload = {
            "name": "company-no-country-tags",
            "link": "https://example.com"
        }
        res = self.client.post(COMPANY_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        company = Company.objects.get(id=res.data['id'])
        self.assertIsNone(company.country)
        self.assertEqual(company.tags.count(), 0)

    def test_duplicate_company_name_same_user_fails(self):
        Company.objects.create(user=self.user, name="dup-company")
        payload = {"name": "dup-company"}
        res = self.client.post(COMPANY_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Trying to create duplicate country.', str(res.data))

    def test_duplicate_company_name_different_users_allowed(self):
        Company.objects.create(user=self.user, name="shared-name")
        other_user = User.objects.create_user(
            email='other@example.com',
            password='pass123'
        )
        self.client.force_authenticate(user=other_user)
        payload = {"name": "shared-name"}
        res = self.client.post(COMPANY_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_tags_are_created_if_not_exist(self):
        payload = {
            "name": "tag-company",
            "tags": ["unique-tag-1", "unique-tag-2"]
        }
        res = self.client.post(COMPANY_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for tag_name in payload['tags']:
            self.assertTrue(Tag.objects.filter(name=tag_name, user=self.user).exists())

    def test_too_many_tags_fails(self):
        payload = {
            "name": "too-many-tags",
            "tags": ["t1", "t2", "t3", "t4", "t5", "t6"]
        }
        res = self.client.post(COMPANY_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Ensure this field has no more than 5 elements.', str(res.data))

    def test_invalid_country_id_fails(self):
        payload = {
            "name": "invalid-country",
            "country": 999999  # non-existent
        }
        res = self.client.post(COMPANY_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('country', res.data)