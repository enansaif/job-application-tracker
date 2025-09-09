# tests/test_interview_api.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
from core.models import Interview, Application, Company, Country, Tag

User = get_user_model()

INTERVIEW_LIST_URL = reverse('interview-list-create')


def interview_detail_url(interview_id: int):
    return reverse('interview-detail', kwargs={'id': interview_id})


def sample_country(user):
    """Create a sample country for testing"""
    idx = Country.objects.filter(user=user).count() + 1
    return Country.objects.create(user=user, name=f'Country {idx}')


def sample_tag(user):
    """Create a sample tag for testing"""
    idx = Tag.objects.filter(user=user).count() + 1
    return Tag.objects.create(user=user, name=f'tag-{idx}')


def sample_company(user):
    """Create a sample company for testing"""
    idx = Company.objects.filter(user=user).count() + 1
    return Company.objects.create(user=user, name=f'Company {idx}')


def sample_application(user):
    """Create a sample application for testing"""
    company = sample_company(user)
    return Application.objects.create(
        user=user,
        company=company,
        position='Software Engineer',
        note='Test application',
        status='applied',
        link='https://example.com/job/123',
    )


def sample_interview(user, application=None):
    """Create a sample interview for testing"""
    if application is None:
        application = sample_application(user)
    return Interview.objects.create(
        user=user,
        application=application,
        date=date.today() + timedelta(days=7),
        note='Test interview note'
    )


class PublicInterviewApiTests(TestCase):
    """Test unauthenticated interview API access"""

    def setUp(self):
        self.client = APIClient()

    def test_list_interviews_requires_auth(self):
        """Test that listing interviews requires authentication"""
        res = self.client.get(INTERVIEW_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_interview_requires_auth(self):
        """Test that creating interviews requires authentication"""
        payload = {
            'application': 1,
            'date': '2024-01-15',
            'note': 'Test interview'
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_interview_requires_auth(self):
        """Test that retrieving interview details requires authentication"""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        interview = sample_interview(user)
        res = self.client.get(interview_detail_url(interview.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_interview_requires_auth(self):
        """Test that updating interviews requires authentication"""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        interview = sample_interview(user)
        payload = {'note': 'Updated note'}
        res = self.client.patch(interview_detail_url(interview.id), payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_interview_requires_auth(self):
        """Test that deleting interviews requires authentication"""
        user = User.objects.create_user(email='test@example.com', password='testpass123')
        interview = sample_interview(user)
        res = self.client.delete(interview_detail_url(interview.id))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateInterviewApiTests(TestCase):
    """Test authenticated interview API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(self.user)

    def test_list_interviews_empty_initially(self):
        """Test listing interviews when none exist"""
        res = self.client.get(INTERVIEW_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_list_interviews_returns_only_user_interviews(self):
        """Test that users only see their own interviews"""
        # Create interview for current user
        interview1 = sample_interview(self.user)
        
        # Create interview for another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass456'
        )
        interview2 = sample_interview(other_user)
        
        res = self.client.get(INTERVIEW_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], interview1.id)

    def test_create_interview_minimal_payload(self):
        """Test creating interview with minimal required fields"""
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': 'Technical interview'
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Check response data
        self.assertIn('id', res.data)
        self.assertEqual(res.data['application']['id'], application.id)
        self.assertEqual(res.data['date'], '2024-01-15')
        self.assertEqual(res.data['note'], 'Technical interview')
        self.assertEqual(res.data['tags'], [])
        
        # Check database
        interview = Interview.objects.get(id=res.data['id'])
        self.assertEqual(interview.user, self.user)
        self.assertEqual(interview.application, application)

    def test_create_interview_with_tags(self):
        """Test creating interview with tags"""
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': 'Technical interview',
            'tags': ['technical', 'onsite', 'final']
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Check tags were created and linked
        interview = Interview.objects.get(id=res.data['id'])
        self.assertEqual(interview.tags.count(), 3)
        tag_names = set(interview.tags.values_list('name', flat=True))
        self.assertEqual(tag_names, {'technical', 'onsite', 'final'})
        
        # Check response includes tags
        returned_tag_names = {tag['name'] for tag in res.data['tags']}
        self.assertEqual(returned_tag_names, {'technical', 'onsite', 'final'})

    def test_create_interview_with_existing_tags(self):
        """Test creating interview with mix of existing and new tags"""
        application = sample_application(self.user)
        existing_tag = sample_tag(self.user)
        
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': 'Technical interview',
            'tags': [existing_tag.name, 'new-tag']
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        interview = Interview.objects.get(id=res.data['id'])
        self.assertEqual(interview.tags.count(), 2)
        tag_names = set(interview.tags.values_list('name', flat=True))
        self.assertEqual(tag_names, {existing_tag.name, 'new-tag'})

    def test_create_interview_with_too_many_tags_fails(self):
        """Test creating interview with more than 5 tags fails"""
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': 'Technical interview',
            'tags': ['tag1', 'tag2', 'tag3', 'tag4', 'tag5', 'tag6']
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tags', res.data)

    def test_create_interview_with_empty_tags_list(self):
        """Test creating interview with empty tags list"""
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': 'Technical interview',
            'tags': []
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        interview = Interview.objects.get(id=res.data['id'])
        self.assertEqual(interview.tags.count(), 0)

    def test_create_interview_invalid_application_id(self):
        """Test creating interview with non-existent application fails"""
        payload = {
            'application': 999999,
            'date': '2024-01-15',
            'note': 'Technical interview'
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('application', res.data)

    def test_create_interview_other_users_application_fails(self):
        """Test creating interview with another user's application fails"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass456'
        )
        other_application = sample_application(other_user)
        
        payload = {
            'application': other_application.id,
            'date': '2024-01-15',
            'note': 'Technical interview'
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('application', res.data)

    def test_create_interview_invalid_date_format(self):
        """Test creating interview with invalid date format fails"""
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': 'invalid-date',
            'note': 'Technical interview'
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', res.data)

    def test_create_interview_missing_required_fields(self):
        """Test creating interview without required fields fails"""
        payload = {'note': 'Technical interview'}
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('application', res.data)
        self.assertIn('date', res.data)

    def test_retrieve_own_interview(self):
        """Test retrieving own interview details"""
        interview = sample_interview(self.user)
        res = self.client.get(interview_detail_url(interview.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], interview.id)
        self.assertIn('application', res.data)
        self.assertIn('tags', res.data)
        self.assertIn('date', res.data)
        self.assertIn('note', res.data)

    def test_retrieve_other_users_interview_404(self):
        """Test retrieving another user's interview returns 404"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass456'
        )
        other_interview = sample_interview(other_user)
        res = self.client.get(interview_detail_url(other_interview.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_nonexistent_interview_404(self):
        """Test retrieving non-existent interview returns 404"""
        res = self.client.get(interview_detail_url(999999))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_interview_basic_fields(self):
        """Test updating interview basic fields"""
        interview = sample_interview(self.user)
        payload = {
            'note': 'Updated interview note',
            'date': '2024-02-15'
        }
        res = self.client.patch(interview_detail_url(interview.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        interview.refresh_from_db()
        self.assertEqual(interview.note, 'Updated interview note')
        self.assertEqual(str(interview.date), '2024-02-15')

    def test_update_interview_tags_replace(self):
        """Test updating interview tags replaces existing tags"""
        interview = sample_interview(self.user)
        tag1 = sample_tag(self.user)
        interview.tags.add(tag1)
        
        payload = {
            'tags': ['new-tag1', 'new-tag2']
        }
        res = self.client.patch(interview_detail_url(interview.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        interview.refresh_from_db()
        self.assertEqual(interview.tags.count(), 2)
        tag_names = set(interview.tags.values_list('name', flat=True))
        self.assertEqual(tag_names, {'new-tag1', 'new-tag2'})

    def test_update_interview_tags_clear_with_empty_list(self):
        """Test updating interview with empty tags list clears tags"""
        interview = sample_interview(self.user)
        tag1 = sample_tag(self.user)
        interview.tags.add(tag1)
        self.assertEqual(interview.tags.count(), 1)
        
        payload = {'tags': []}
        res = self.client.patch(interview_detail_url(interview.id), payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        interview.refresh_from_db()
        self.assertEqual(interview.tags.count(), 0)

    def test_update_interview_without_tags_keeps_existing(self):
        """Test updating interview without tags field keeps existing tags"""
        interview = sample_interview(self.user)
        tag1 = sample_tag(self.user)
        interview.tags.add(tag1)
        
        payload = {'note': 'Updated note only'}
        res = self.client.patch(interview_detail_url(interview.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        interview.refresh_from_db()
        self.assertEqual(interview.tags.count(), 1)
        self.assertEqual(interview.tags.first().name, tag1.name)

    def test_update_interview_application(self):
        """Test updating interview application"""
        interview = sample_interview(self.user)
        new_application = sample_application(self.user)
        
        payload = {'application': new_application.id}
        res = self.client.patch(interview_detail_url(interview.id), payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        interview.refresh_from_db()
        self.assertEqual(interview.application, new_application)

    def test_update_interview_invalid_application_fails(self):
        """Test updating interview with invalid application fails"""
        interview = sample_interview(self.user)
        payload = {'application': 999999}
        res = self.client.patch(interview_detail_url(interview.id), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('application', res.data)

    def test_update_other_users_interview_404(self):
        """Test updating another user's interview returns 404"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass456'
        )
        other_interview = sample_interview(other_user)
        payload = {'note': 'Hacked note'}
        res = self.client.patch(interview_detail_url(other_interview.id), payload)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_own_interview(self):
        """Test deleting own interview"""
        interview = sample_interview(self.user)
        res = self.client.delete(interview_detail_url(interview.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Interview.objects.filter(id=interview.id).exists())

    def test_delete_other_users_interview_404(self):
        """Test deleting another user's interview returns 404"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass456'
        )
        other_interview = sample_interview(other_user)
        res = self.client.delete(interview_detail_url(other_interview.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_interview_404(self):
        """Test deleting non-existent interview returns 404"""
        res = self.client.delete(interview_detail_url(999999))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_interview_tags_are_user_scoped(self):
        """Test that interview tags are created under the correct user"""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass456'
        )
        other_tag = Tag.objects.create(user=other_user, name='other-tag')
        
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': 'Technical interview',
            'tags': ['other-tag', 'my-tag']
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Check that a new tag was created for current user, not reused other's tag
        interview = Interview.objects.get(id=res.data['id'])
        my_tags = interview.tags.filter(user=self.user)
        self.assertEqual(my_tags.count(), 2)
        
        # Should have created new tags, not reused other user's tag
        self.assertTrue(Tag.objects.filter(user=self.user, name='other-tag').exists())
        self.assertTrue(Tag.objects.filter(user=self.user, name='my-tag').exists())
        self.assertEqual(Tag.objects.filter(name='other-tag').count(), 2)  # One for each user

    def test_interview_serializer_response_format(self):
        """Test that interview response includes all expected fields"""
        application = sample_application(self.user)
        tag = sample_tag(self.user)
        interview = sample_interview(self.user, application)
        interview.tags.add(tag)
        
        res = self.client.get(interview_detail_url(interview.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        # Check response structure
        expected_fields = ['id', 'application', 'tags', 'date', 'note']
        for field in expected_fields:
            self.assertIn(field, res.data)
        
        # Check application detail structure
        self.assertIn('id', res.data['application'])
        self.assertIn('company', res.data['application'])
        self.assertIn('position', res.data['application'])
        
        # Check tags structure
        self.assertIsInstance(res.data['tags'], list)
        if res.data['tags']:
            self.assertIn('id', res.data['tags'][0])
            self.assertIn('name', res.data['tags'][0])

    def test_interview_date_validation(self):
        """Test various date validation scenarios"""
        application = sample_application(self.user)
        
        # Test past date (should be allowed)
        payload = {
            'application': application.id,
            'date': '2020-01-01',
            'note': 'Past interview'
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        # Test future date
        future_date = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        payload = {
            'application': application.id,
            'date': future_date,
            'note': 'Future interview'
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_interview_note_optional(self):
        """Test that interview note can be empty"""
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': ''
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        interview = Interview.objects.get(id=res.data['id'])
        self.assertEqual(interview.note, '')

    def test_interview_with_max_tags(self):
        """Test creating interview with maximum allowed tags (5)"""
        application = sample_application(self.user)
        payload = {
            'application': application.id,
            'date': '2024-01-15',
            'note': 'Technical interview',
            'tags': ['tag1', 'tag2', 'tag3', 'tag4', 'tag5']
        }
        res = self.client.post(INTERVIEW_LIST_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        
        interview = Interview.objects.get(id=res.data['id'])
        self.assertEqual(interview.tags.count(), 5)
