# Generated by Django 5.1.5 on 2025-03-25 23:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_rename_nombre_pedido_reclamacion_numero_pedido'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsletterSubscriber',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=255, unique=True)),
                ('subscribed_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Suscriptor de Newsletter',
                'verbose_name_plural': 'Suscriptores de Newsletter',
            },
        ),
    ]
