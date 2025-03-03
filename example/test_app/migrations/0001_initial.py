# Generated by Django 1.11.5 on 2017-11-21 18:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Ad",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("created", models.DateField(auto_now_add=True)),
                ("modified", models.DateField(auto_now=True)),
                ("url", models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name="Car",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("launched", models.DateField()),
                (
                    "type",
                    models.CharField(
                        choices=[("se", "Sedan"), ("br", "Break"), ("4x", "4x4"), ("co", "Coupé")],
                        default="se",
                        max_length=2,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("slug", models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Manufacturer",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("country_code", models.CharField(max_length=2)),
                ("logo", models.ImageField(blank=True, upload_to="")),
                ("created", models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name="car",
            name="categories",
            field=models.ManyToManyField(to="test_app.Category"),
        ),
        migrations.AddField(
            model_name="car",
            name="manufacturer",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="test_app.Manufacturer"),
        ),
        migrations.AddField(
            model_name="ad",
            name="car",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="ads", to="test_app.Car"
            ),
        ),
    ]
