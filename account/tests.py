from django.test import TestCase
from django.urls import reverse

from .models import User


class LoginWhitespaceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='reader@example.com',
            email='reader@example.com',
            mobile='9876543210',
            user_type='subscriber',
            password='secret123',
        )

    def test_login_ignores_spaces_in_email(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': ' reader@example.com ',
                'password': 'secret123',
            }
        )

        self.assertRedirects(response, reverse('profile'))

    def test_login_ignores_spaces_in_mobile(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': '98765 43210',
                'password': 'secret123',
            }
        )

        self.assertRedirects(response, reverse('profile'))

    def test_login_ignores_outer_spaces_in_password(self):
        response = self.client.post(
            reverse('login'),
            {
                'username': '9876543210',
                'password': ' secret123 ',
            }
        )

        self.assertRedirects(response, reverse('profile'))

    def test_text_fields_are_trimmed_before_save(self):
        user = User.objects.create_user(
            username='  trimmed-user  ',
            email='  trimmed@example.com  ',
            mobile='  9000000001  ',
            first_name='  Trimmed  ',
            last_name='  Reader  ',
            full_name='  Trimmed Reader  ',
            address='  Trimmed Address  ',
            city='  Mathura  ',
            district='  Mathura  ',
            state='  Uttar Pradesh  ',
            pincode='  281001  ',
            country='  India  ',
            user_type='  subscriber  ',
            password='secret123',
        )

        user.refresh_from_db()
        self.assertEqual(user.username, 'trimmed-user')
        self.assertEqual(user.email, 'trimmed@example.com')
        self.assertEqual(user.mobile, '9000000001')
        self.assertEqual(user.first_name, 'Trimmed')
        self.assertEqual(user.last_name, 'Reader')
        self.assertEqual(user.full_name, 'Trimmed Reader')
        self.assertEqual(user.address, 'Trimmed Address')
        self.assertEqual(user.city, 'Mathura')
        self.assertEqual(user.district, 'Mathura')
        self.assertEqual(user.state, 'Uttar Pradesh')
        self.assertEqual(user.pincode, '281001')
        self.assertEqual(user.country, 'India')
        self.assertEqual(user.user_type, 'subscriber')
