from django.test import TestCase
from .models import User


class MobilePasswordTests(TestCase):
    def test_manager_and_direct_creation_use_mobile(self):
        user = User.objects.create_user(username='reader', mobile='+91 98765 43210', password='random')
        self.assertTrue(user.check_password('9876543210'))
        self.assertNotEqual(user.password, '9876543210')
        direct = User.objects.create(username='direct', mobile='9000000000')
        self.assertTrue(direct.check_password('9000000000'))

    def test_updates_preserve_changed_password(self):
        user = User.objects.create_user(username='reader', mobile='9876543210')
        user.set_password('changed-password')
        user.save()
        user.mobile = '9000000000'
        user.save()
        user.refresh_from_db()
        self.assertTrue(user.check_password('changed-password'))

    def test_admin_and_accounts_without_mobile_keep_password(self):
        for index, fields in enumerate(({'is_staff': True, 'mobile': '9876543210'},
                                       {'is_superuser': True, 'mobile': '9876543210'}, {})):
            user = User.objects.create_user(username=f'user{index}', password='chosen-password', **fields)
            self.assertTrue(user.check_password('chosen-password'))
