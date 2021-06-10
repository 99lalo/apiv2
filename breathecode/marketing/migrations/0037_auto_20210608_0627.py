# Generated by Django 3.2 on 2021-06-08 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0036_alter_academyalias_academy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formentry',
            name='course',
            field=models.CharField(default=None, max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='formentry',
            name='location',
            field=models.CharField(blank=True, default=None, max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='formentry',
            name='referral_key',
            field=models.CharField(blank=True, default=None, max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='formentry',
            name='utm_campaign',
            field=models.CharField(blank=True, default=None, max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='formentry',
            name='utm_medium',
            field=models.CharField(blank=True, default=None, max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='formentry',
            name='utm_source',
            field=models.CharField(blank=True, default=None, max_length=70, null=True),
        ),
    ]
