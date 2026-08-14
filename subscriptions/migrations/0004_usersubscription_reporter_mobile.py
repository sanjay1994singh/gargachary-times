from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0003_invoice_delivery_note_invoice_delivery_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='reporter_mobile',
            field=models.CharField(
                blank=True,
                help_text='Mobile number of the reporter who sold this subscription.',
                max_length=20
            ),
        ),
    ]
