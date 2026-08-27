from importlib.metadata import PackageNotFoundError, version

from django.utils.module_loading import autodiscover_modules

from .documents import Document
from .fields import (
    BooleanField,
    ByteField,
    CompletionField,
    DateField,
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
    OSField,
    ScaledFloatField,
    SearchAsYouTypeField,
    ShortField,
    TextField,
    TimeField,
)
from .indices import Index

# Derived from the installed distribution so pyproject.toml is the single place
# the version is written, rather than a literal duplicated across modules that
# can drift apart.
try:
    __version__ = version("django-opensearch-models")
except PackageNotFoundError:  # pragma: no cover - running from a source tree with no install
    __version__ = "0.0.0.dev0"


__all__ = [
    "BooleanField",
    "ByteField",
    "CompletionField",
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
    "OSField",
    "ObjectField",
    "ScaledFloatField",
    "SearchAsYouTypeField",
    "ShortField",
    "TextField",
    "TimeField",
    "__version__",
]


def autodiscover():
    autodiscover_modules("documents")
