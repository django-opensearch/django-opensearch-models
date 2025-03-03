from django.utils.module_loading import autodiscover_modules

from .documents import Document
from .fields import (
    BooleanField,
    ByteField,
    CompletionField,
    DateField,
    DEDField,
    DoubleField,
    FileField,
    FileFieldMixin,
    FloatField,
    GeoPointField,
    GeoShapeField,
    IntegerField,
    IpField,
    KeywordField,
    ListField,
    LongField,
    NestedField,
    ObjectField,
    ScaledFloatField,
    SearchAsYouTypeField,
    ShortField,
    TextField,
    TimeField,
)
from .indices import Index

__version__ = "1.0.0"


__all__ = [
    "BooleanField",
    "ByteField",
    "CompletionField",
    "DEDField",
    "DateField",
    "Document",
    "DoubleField",
    "FileField",
    "FileFieldMixin",
    "FloatField",
    "GeoPointField",
    "GeoShapeField",
    "Index",
    "IntegerField",
    "IpField",
    "KeywordField",
    "ListField",
    "LongField",
    "NestedField",
    "ObjectField",
    "ScaledFloatField",
    "SearchAsYouTypeField",
    "ShortField",
    "TextField",
    "TimeField",
]


def autodiscover():
    autodiscover_modules("documents")
