from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bankloan', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='creditcardloanledger',
            name='principal_amount',
        ),
        migrations.RemoveField(
            model_name='creditcardloanledger',
            name='principal_paid',
        ),
        migrations.RemoveField(
            model_name='creditcardloanledger',
            name='interest_paid',
        ),
        migrations.RemoveField(
            model_name='creditcardloanledger',
            name='total_paid',
        ),
        migrations.RemoveField(
            model_name='creditcardloanledger',
            name='payment_rate_percent',
        ),
        migrations.RemoveField(
            model_name='creditcardloanledger',
            name='days_from_last_payment',
        ),
        migrations.AddField(
            model_name='creditcardloanledger',
            name='payment_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
