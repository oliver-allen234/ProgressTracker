# Generated by Django 5.2.1 on 2025-07-02 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='completed_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usertask',
            name='completed_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
