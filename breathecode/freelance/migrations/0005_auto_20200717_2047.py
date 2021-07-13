# Generated by Django 3.0.8 on 2020-07-17 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('freelance', '0004_issue_duration_in_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='total_duration_in_hours',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='bill',
            name='paid_at',
            field=models.DateTimeField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='total_duration_in_minutes',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='bill',
            name='total_price',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='issue',
            name='status',
            field=models.CharField(choices=[
                ('IGNORED', 'Ignored'), ('DRAFT', 'Draft'), ('TODO', 'Todo'),
                ('DOING', 'Doing'), ('DONE', 'Done')
            ],
                                   default='DRAFT',
                                   max_length=20),
        ),
    ]
