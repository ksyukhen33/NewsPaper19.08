# Generated by Django 4.2.11 on 2024-07-10 19:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_remove_subscription_category_subscription_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='Category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscriptions', to='news.category'),
        ),
    ]