from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Tag
from django.contrib.auth import get_user_model
from django.urls import reverse

URL = reverse('tags-list-create')

User = get_user_model()

def get_tag_detail_url(id):
    return reverse('tags-update-destroy', kwargs={'id': id})


class PublicTagTestCases(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_restrict_unauthenticated_user(self):
        response = self.client.post(URL, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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
        self.assertNotIn('user', response.data)

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

    def test_create_duplicate_tag_unsuccessful(self):
        payload = {'name': 'hifi'}
        res1 = self.client.post(URL, payload)
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        res2 = self.client.post(URL, payload)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_tag_successful(self):
        create_res = self.client.post(URL, {'name': 'hifi'})
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        tag_id = create_res.data['id']
        payload = {'name': 'important'}
        update_res = self.client.patch(get_tag_detail_url(tag_id), payload)
        self.assertEqual(update_res.status_code, status.HTTP_200_OK)
        self.assertIn('name', update_res.data)
        self.assertEqual(update_res.data['name'], payload['name'])

    def test_delete_tag_successful(self):
        res = self.client.post(URL, {'name': 'temp'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tag_id = res.data['id']
        self.assertEqual(Tag.objects.filter(user=self.user).count(), 1)
        del_res = self.client.delete(get_tag_detail_url(tag_id))
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Tag.objects.filter(user=self.user).count(), 0)

    def test_delete_other_users_tag_unsuccessful(self):
        res = self.client.post(URL, {'name': 'private'})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        tag_id = res.data['id']
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass456'
        )
        self.client.force_authenticate(user=other_user)
        del_res = self.client.delete(get_tag_detail_url(tag_id))
        self.assertEqual(del_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_tag_with_whitespace_trimmed(self):
        payload = {'name': 'hifi      '}
        response = self.client.post(URL, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'), payload['name'].strip())


