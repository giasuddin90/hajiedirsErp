from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bankloan', '0002_simplify_loan_ledger'),
    ]

    operations = [
        migrations.AddField(
            model_name='creditcardloanledger',
            name='interest_paid',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
        ),
    ]
