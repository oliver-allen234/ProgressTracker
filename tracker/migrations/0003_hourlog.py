
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_usertask'),
    ]

    operations = [
        migrations.CreateModel(
            name='HourLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('hours', models.DecimalField(decimal_places=2, max_digits=5)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('goal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hour_logs', to='tracker.goal')),
            ],
            options={
                'verbose_name': 'Hour Log',
                'verbose_name_plural': 'Hour Logs',
                'ordering': ['-date'],
            },
        ),
    ]
