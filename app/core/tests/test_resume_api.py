# tests/test_resume_api.py
from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from core.models import Tag
from core.models import Resume  # adjust import path if different
import io
import tempfile
import shutil
from django.conf import settings

User = get_user_model()

RESUME_LIST_URL = reverse('resume-list-create')


def resume_detail_url(resume_id: int):
    return reverse('resume-update', kwargs={'id': resume_id})


def make_dummy_file(name="cv.pdf", content=b"%PDF-1.4\n%..."):
    # minimal PDF-like bytes; adjust as needed
    return SimpleUploadedFile(name=name, content=content, content_type="application/pdf")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PublicResumeApiTests(TestCase):
    """Unauthenticated access tests"""

    @classmethod
    def tearDownClass(cls):
        # Clean temporary MEDIA_ROOT
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()

    def test_list_requires_auth(self):
        res = self.client.get(RESUME_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_auth(self):
        file = make_dummy_file()
        res = self.client.post(RESUME_LIST_URL, {'file': file}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PrivateResumeApiTests(TestCase):
    """Authenticated access tests"""

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="test@example.com", password="pass12345")
        self.client.force_authenticate(self.user)

    # ------- List / Detail -------

    def test_list_initially_empty(self):
        res = self.client.get(RESUME_LIST_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, [])

    def test_list_returns_only_current_user_resumes(self):
        # Create resume for self.user
        my_file = make_dummy_file()
        res1 = self.client.post(RESUME_LIST_URL, {'file': my_file}, format='multipart')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Create resume for another user
        other = User.objects.create_user(email="other@example.com", password="pass67890")
        other_client = APIClient()
        other_client.force_authenticate(other)
        other_file = make_dummy_file(name="other.pdf")
        res2 = other_client.post(RESUME_LIST_URL, {'file': other_file}, format='multipart')
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        # List as self.user
        res_list = self.client.get(RESUME_LIST_URL)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 1)
        self.assertEqual(res_list.data[0]['id'], res1.data['id'])
        self.assertIn('tags', res_list.data[0])  # Read serializer includes tags list

    def test_detail_only_owner_can_view(self):
        # Create resume for self.user
        my_file = make_dummy_file()
        created = self.client.post(RESUME_LIST_URL, {'file': my_file}, format='multipart')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        resume_id = created.data['id']

        # Another user tries to view detail -> 404
        other = User.objects.create_user(email="other2@example.com", password="pass456")
        other_client = APIClient()
        other_client.force_authenticate(other)
        res = other_client.get(resume_detail_url(resume_id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

        # Owner can view detail
        res_owner = self.client.get(resume_detail_url(resume_id))
        self.assertEqual(res_owner.status_code, status.HTTP_200_OK)
        self.assertEqual(res_owner.data['id'], resume_id)

    # ------- Create -------

    def test_create_resume_without_tags(self):
        file = make_dummy_file(name="cv1.pdf")
        res = self.client.post(RESUME_LIST_URL, {'file': file}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', res.data)
        self.assertNotIn('file', res.data)
        self.assertEqual(res.data['tags'], [])
        self.assertEqual(Resume.objects.filter(user=self.user).count(), 1)

    def test_create_resume_with_tags_creates_and_links(self):
        file = make_dummy_file(name="cv2.pdf")
        payload = {
            'file': file,
            'tags': ['job', 'urgent', 'senior']
        }
        res = self.client.post(RESUME_LIST_URL, data=payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        resume_id = res.data['id']
        resume = Resume.objects.get(id=resume_id, user=self.user)
        # Read serializer returns list of tag objects
        returned_tags = {t['name'] for t in res.data['tags']}
        self.assertSetEqual(returned_tags, set(payload['tags']))

        # Tag objects exist and are linked
        self.assertEqual(resume.tags.count(), 3)
        for name in payload['tags']:
            self.assertTrue(Tag.objects.filter(user=self.user, name=name).exists())

    def test_create_resume_with_existing_and_new_tags(self):
        # Pre-create one tag
        Tag.objects.create(user=self.user, name='urgent')
        file = make_dummy_file(name="cv3.pdf")
        payload = {'file': file, 'tags': ['urgent', 'backend']}
        res = self.client.post(RESUME_LIST_URL, data=payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        resume = Resume.objects.get(id=res.data['id'])
        names = set(resume.tags.values_list('name', flat=True))
        self.assertSetEqual(names, {'urgent', 'backend'})

    def test_create_resume_with_too_many_tags_fails(self):
        file = make_dummy_file(name="cv4.pdf")
        payload = {'file': file, 'tags': ['a', 'b', 'c', 'd', 'e', 'f']}  # 6 > max_length=5
        res = self.client.post(RESUME_LIST_URL, data=payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('tags', res.data)

    def test_create_resume_with_non_list_tags_treated_as_single_tag(self):
        file = make_dummy_file(name="cv5.pdf")
        # strings will be parsed as JSON array only if sent as JSON; multipart keeps it as string -> should error
        payload = {'file': file, 'tags': 'not-a-list'}
        res = self.client.post(RESUME_LIST_URL, data=payload, format='multipart')
        self.assertIn('tags', res.data)
        self.assertEqual(res.data['tags'][0]['name'], 'not-a-list')

    def test_create_resume_without_file_fails(self):
        res = self.client.post(RESUME_LIST_URL, data={'tags': ['one']}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', res.data)

    def test_create_resume_tags_are_scoped_per_user(self):
        # Create same tag name for another user first
        other = User.objects.create_user(email="owner@else.com", password="passxxx")
        Tag.objects.create(user=other, name='shared')

        file = make_dummy_file(name="cv6.pdf")
        res = self.client.post(RESUME_LIST_URL, data={'file': file, 'tags': ['shared']}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Ensure my Tag was created under my user context, not reusing other's
        self.assertTrue(Tag.objects.filter(user=self.user, name='shared').exists())
        self.assertEqual(Tag.objects.filter(name='shared').count(), 2)

    # ------- PATCH (current behavior in your view) -------

    def test_patch_returns_204_and_does_not_persist_changes_current_behavior(self):
        """
        As implemented, ResumeDetailView.patch:
        - Builds serializer WITHOUT context
        - Calls serializer.is_valid() but NEVER .save()
        - Returns 204 NO CONTENT
        => No changes are persisted. This test locks the current behavior.
        """
        # Create resume with initial tags
        res_create = self.client.post(
            RESUME_LIST_URL,
            data={'file': make_dummy_file('cv7.pdf'), 'tags': ['first']},
            format='multipart'
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        resume_id = res_create.data['id']

        # Attempt to update tags
        patch_payload = {'tags': ['updated', 'second']}
        res_patch = self.client.patch(resume_detail_url(resume_id), data=patch_payload, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(res_patch.data, None)  # No body on 204

        # Fetch detail again: tags should be unchanged due to missing .save()
        res_detail = self.client.get(resume_detail_url(resume_id))
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        names = {t['name'] for t in res_detail.data['tags']}
        self.assertSetEqual(names, {'first'})

    # ------- Permissions on PATCH -------

    def test_patch_other_users_resume_forbidden_404(self):
        # Create resume for another user
        other = User.objects.create_user(email="nope@example.com", password="passxxx")
        other_client = APIClient()
        other_client.force_authenticate(other)
        created = other_client.post(RESUME_LIST_URL, data={'file': make_dummy_file('cv8.pdf')}, format='multipart')
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        other_resume_id = created.data['id']

        # Self tries to patch other's resume -> 404 (get_object_or_404 with user=request.user)
        res = self.client.patch(resume_detail_url(other_resume_id), data={'tags': ['x']}, format='json')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
