from django.db import migrations


def set_subscriber_user_type(apps, schema_editor):
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    User = apps.get_model('account', 'User')

    subscriber_ids = (
        UserSubscription.objects
        .filter(payment_status='SUCCESS', is_active=True)
        .values_list('user_id', flat=True)
        .distinct()
    )

    User.objects.filter(id__in=subscriber_ids).update(user_type='subscriber')


def unset_subscriber_user_type(apps, schema_editor):
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    User = apps.get_model('account', 'User')

    subscriber_ids = (
        UserSubscription.objects
        .filter(payment_status='SUCCESS', is_active=True)
        .values_list('user_id', flat=True)
        .distinct()
    )

    User.objects.filter(id__in=subscriber_ids, user_type='subscriber').update(user_type=None)


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_country_state_user_address_user_country_user_full_name_user_pincode'),
        ('subscriptions', '0004_usersubscription_reporter_mobile'),
    ]

    operations = [
        migrations.RunPython(
            set_subscriber_user_type,
            unset_subscriber_user_type
        ),
    ]
