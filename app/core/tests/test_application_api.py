# tests/test_application_api.py

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from core.models import Application, Company, Country, Tag, Resume

CREATE_URL = reverse('app-create')


def detail_url(app_id: int):
    return reverse('app-detail', kwargs={'id': app_id})


User = get_user_model()


def sample_country(user):
    idx = Country.objects.filter(user=user).count() + 1
    return Country.objects.create(user=user, name=f'Country {idx}')


def sample_tag(user):
    idx = Tag.objects.filter(user=user).count() + 1
    return Tag.objects.create(user=user, name=f'tag-{idx}')


def sample_company(user):
    idx = Company.objects.filter(user=user).count() + 1
    return Company.objects.create(user=user, name=f'Company {idx}')


def sample_resume(user):
    idx = Resume.objects.filter(user=user).count() + 1
    file_obj = SimpleUploadedFile(f'resume-{idx}.pdf', b'PDF bytes', content_type='application/pdf')
    return Resume.objects.create(user=user, file=file_obj)


def sample_application(user):
    company = sample_company(user)
    return Application.objects.create(
        user=user,
        company=company,
        position='Software Engineer',
        note='Submitted via portal',
        status='applied',
        link='https://jobs.example.com/123',
    )


class PublicApplicationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required_for_create(self):
        res = self.client.post(CREATE_URL, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_detail_get(self):
        user = User.objects.create_user(email='u@example.com', password='testpass123')
        app = sample_application(user)
        res = self.client.get(detail_url(app.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_update(self):
        user = User.objects.create_user(email='u2@example.com', password='testpass123')
        app = sample_application(user)
        res = self.client.patch(detail_url(app.id), {'position': 'Senior SE'})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateApplicationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)

    def test_create_application_minimal_payload(self):
        company = sample_company(self.user)
        payload = {
            'company_id': company.id,
            'position': 'Backend Engineer',
            'status': 'applied',
            'note': 'Applied via careers page',
        }
        res = self.client.post(CREATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', res.data)
        self.assertIn('company', res.data)
        self.assertEqual(res.data['company']['id'], company.id)
        self.assertEqual(res.data['position'], payload['position'])
        self.assertEqual(res.data['status'], payload['status'])
        for k in ('company_id', 'country_id', 'tag_ids', 'resume_id'):
            self.assertNotIn(k, res.data)
        self.assertIn('created_at', res.data)
        self.assertIn('updated_at', res.data)
        app = Application.objects.get(id=res.data['id'])
        self.assertEqual(app.user, self.user)
        self.assertEqual(app.company, company)
        self.assertEqual(app.position, 'Backend Engineer')

    def test_create_with_optional_country_resume_and_tags(self):
        company = sample_company(self.user)
        country = sample_country(self.user)
        resume = sample_resume(self.user)
        tag1 = sample_tag(self.user)
        tag2 = sample_tag(self.user)
        payload = {
            'company_id': company.id,
            'country_id': country.id,
            'resume_id': resume.id,
            'tag_ids': [tag1.id, tag2.id],
            'position': 'Data Engineer',
            'status': 'applied',
            'link': 'https://example.com/job/de-1',
            'note': 'Recruiter call scheduled',
        }
        res = self.client.post(CREATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        app = Application.objects.get(id=res.data['id'])
        self.assertEqual(app.country, country)
        self.assertEqual(app.resume, resume)
        self.assertEqual(set(app.tags.values_list('id', flat=True)), {tag1.id, tag2.id})
        self.assertIn('country', res.data)
        self.assertEqual(res.data['country']['id'], country.id)
        self.assertIn('tags', res.data)
        self.assertEqual(sorted([t['id'] for t in res.data['tags']]), sorted([tag1.id, tag2.id]))

    def test_create_invalid_company_id(self):
        payload = {'company_id': 999999, 'position': 'QA', 'status': 'applied'}
        res = self.client.post(CREATE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('company' in res.data or 'company_id' in res.data)

    def test_create_with_empty_tag_list_clears_tags(self):
        company = sample_company(self.user)
        payload = {
            'company_id': company.id,
            'position': 'Analyst',
            'status': 'applied',
            'tag_ids': [],
        }
        res = self.client.post(CREATE_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        app = Application.objects.get(id=res.data['id'])
        self.assertEqual(app.tags.count(), 0)

    def test_retrieve_own_application(self):
        app = sample_application(self.user)
        res = self.client.get(detail_url(app.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], app.id)
        self.assertIn('company', res.data)
        self.assertIn('country', res.data)
        self.assertIn('tags', res.data)
        for k in ('company_id', 'country_id', 'tag_ids', 'resume_id'):
            self.assertNotIn(k, res.data)

    def test_retrieve_other_users_application_404(self):
        other = User.objects.create_user(email='other@example.com', password='pass12345')
        app = sample_application(other)
        res = self.client.get(detail_url(app.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_update_basic_fields(self):
        app = sample_application(self.user)
        payload = {'position': 'SWE II', 'note': 'Updated note', 'status': 'interviewing'}
        res = self.client.patch(detail_url(app.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.position, 'SWE II')
        self.assertEqual(app.note, 'Updated note')
        self.assertEqual(app.status, 'interviewing')

    def test_update_company_and_country_via_ids(self):
        app = sample_application(self.user)
        new_company = sample_company(self.user)
        new_country = sample_country(self.user)
        payload = {'company_id': new_company.id, 'country_id': new_country.id}
        res = self.client.patch(detail_url(app.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.company, new_company)
        self.assertEqual(app.country, new_country)
        self.assertEqual(res.data['company']['id'], new_company.id)
        self.assertEqual(res.data['country']['id'], new_country.id)

    def test_update_tags_replace_set(self):
        app = sample_application(self.user)
        t1 = sample_tag(self.user)
        t2 = sample_tag(self.user)
        t3 = sample_tag(self.user)
        res1 = self.client.patch(detail_url(app.id), {'tag_ids': [t1.id, t2.id]})
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(set(app.tags.values_list('id', flat=True)), {t1.id, t2.id})
        res2 = self.client.patch(detail_url(app.id), {'tag_ids': [t3.id]})
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(set(app.tags.values_list('id', flat=True)), {t3.id})
        self.assertEqual([t['id'] for t in res2.data['tags']], [t3.id])

    def test_update_tags_clear_when_empty_list(self):
        app = sample_application(self.user)
        t1 = sample_tag(self.user)
        app.tags.add(t1)
        self.assertEqual(app.tags.count(), 1)
        res = self.client.patch(detail_url(app.id), {'tag_ids': []}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(app.tags.count(), 0)

    def test_update_without_tag_ids_keeps_existing_tags(self):
        app = sample_application(self.user)
        t1 = sample_tag(self.user)
        app.tags.add(t1)
        res = self.client.patch(detail_url(app.id), {'note': 'touch other fields'})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.assertEqual(set(app.tags.values_list('id', flat=True)), {t1.id})

    def test_update_invalid_company_id(self):
        app = sample_application(self.user)
        res = self.client.patch(detail_url(app.id), {'company_id': 999999})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue('company' in res.data or 'company_id' in res.data)

    def test_update_other_users_application_404(self):
        other = User.objects.create_user(email='other@example.com', password='pass12345')
        app = sample_application(other)
        res = self.client.patch(detail_url(app.id), {'position': 'Nope'})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_updated_at_changes_after_update(self):
        app = sample_application(self.user)
        res_get_1 = self.client.get(detail_url(app.id))
        self.assertEqual(res_get_1.status_code, status.HTTP_200_OK)
        first_updated_at = res_get_1.data['updated_at']
        res_patch = self.client.patch(detail_url(app.id), {'note': 'v2'})
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        res_get_2 = self.client.get(detail_url(app.id))
        self.assertEqual(res_get_2.status_code, status.HTTP_200_OK)
        self.assertNotEqual(first_updated_at, res_get_2.data['updated_at'])
