from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_country_state_user_address_user_country_user_full_name_user_pincode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
    ]
