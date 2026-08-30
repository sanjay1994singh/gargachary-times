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
