# Generated by Django 3.2.9 on 2023-06-04 10:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PDF',
            fields=[
                ('srno', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Entity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255)),
                ('text', models.TextField()),
                ('pdf', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='home.pdf')),
            ],
        ),
    ]
