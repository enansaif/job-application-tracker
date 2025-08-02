from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class PublicTestCase(TestCase):

    def test_create_user_email_successful(self):
        email = 'user@example.com'
        password = 'test1234'
        name = 'test_user'
        user = User.objects.create_user(
            email=email,
            password=password,
            name=name,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertFalse(user.is_staff)
        self.assertEqual(user.name, name)

    def test_create_superuser_email_successful(self):
        email = 'user@example.com'
        password = 'test1234'
        user = User.objects.create_superuser(
            email=email,
            password=password,
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_create_user_no_email_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='')

    def test_create_user_invalid_email_error(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='test.com')
