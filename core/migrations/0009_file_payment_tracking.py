# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20250910_0053'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='file',
            name='payment_method',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='file',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
