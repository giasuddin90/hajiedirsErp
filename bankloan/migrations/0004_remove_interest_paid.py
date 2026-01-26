from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bankloan', '0003_add_interest_paid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='creditcardloanledger',
            name='interest_paid',
        ),
    ]
