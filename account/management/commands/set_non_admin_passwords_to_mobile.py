from django.core.management.base import BaseCommand

from account.models import User


def get_mobile_password(mobile):
    digits = ''.join(
        char
        for char in (mobile or '')
        if char.isdigit()
    )

    if len(digits) >= 10:
        return digits[-10:]

    return digits


class Command(BaseCommand):
    help = 'Set every non-admin user password to the last 10 digits of their mobile number.'

    def handle(self, *args, **options):
        users = (
            User.objects
            .filter(is_staff=False, is_superuser=False)
            .exclude(mobile__isnull=True)
            .exclude(mobile='')
        )
        updated_count = 0

        for user in users.iterator():
            mobile_password = get_mobile_password(user.mobile)

            if not mobile_password:
                continue

            user.set_password(mobile_password)
            user.save(update_fields=['password'])
            updated_count += 1

        skipped_count = (
            User.objects
            .filter(is_staff=False, is_superuser=False)
            .filter(mobile__isnull=True)
            .count()
        )
        skipped_count += (
            User.objects
            .filter(is_staff=False, is_superuser=False, mobile='')
            .count()
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Updated {updated_count} non-admin user passwords. '
                f'Skipped {skipped_count} users without mobile numbers.'
            )
        )
