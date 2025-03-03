from django.db import models
from django.utils.translation import gettext_lazy as _


class Car(models.Model):
    TYPE_CHOICES = (
        ("se", "Sedan"),
        ("br", "Break"),
        ("4x", "4x4"),
        ("co", "Coupé"),
    )

    name = models.CharField(max_length=255)
    launched = models.DateField()
    type = models.CharField(
        max_length=2,
        choices=TYPE_CHOICES,
        default="se",
    )
    manufacturer = models.ForeignKey("Manufacturer", null=True, on_delete=models.SET_NULL)
    categories = models.ManyToManyField("Category")

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.name


COUNTRIES = {
    "FR": "France",
    "UK": "United Kingdom",
    "ES": "Spain",
    "IT": "Italya",
}


class Manufacturer(models.Model):
    name = models.CharField(max_length=255, default=_("Test lazy tanslation"))
    country_code = models.CharField(max_length=2)
    created = models.DateField()
    logo = models.ImageField(blank=True)

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.name

    def country(self):
        return COUNTRIES.get(self.country_code, self.country_code)


class Category(models.Model):
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)
    icon = models.ImageField(blank=True)

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.title


class Ad(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    created = models.DateField(auto_now_add=True)
    modified = models.DateField(auto_now=True)
    url = models.URLField()
    car = models.ForeignKey("Car", related_name="ads", null=True, on_delete=models.SET_NULL)

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.title


class Article(models.Model):
    slug = models.CharField(
        max_length=255,
        unique=True,
    )

    class Meta:
        app_label = "tests"

    def __str__(self):
        return self.slug
