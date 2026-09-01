from importlib.metadata import PackageNotFoundError, version

from django.utils.module_loading import autodiscover_modules

from .documents import Document
from .fields import (
    BooleanField,
    ByteField,
    CompletionField,
    DateField,
    DateRangeField,
    DoubleField,
    DoubleRangeField,
    FileField,
    FileFieldMixin,
    FloatField,
    FloatRangeField,
    GeoPointField,
    GeoShapeField,
    IntegerField,
    IntegerRangeField,
    IpField,
    IpRangeField,
    KeywordField,
    KnnVectorField,
    ListField,
    LongField,
    LongRangeField,
    NestedField,
    ObjectField,
    OSField,
    RankFeatureField,
    RankFeaturesField,
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
    "DateRangeField",
    "Document",
    "DoubleField",
    "DoubleRangeField",
    "FileField",
    "FileFieldMixin",
    "FloatField",
    "FloatRangeField",
    "GeoPointField",
    "GeoShapeField",
    "Index",
    "IntegerField",
    "IntegerRangeField",
    "IpField",
    "IpRangeField",
    "KeywordField",
    "KnnVectorField",
    "ListField",
    "LongField",
    "LongRangeField",
    "NestedField",
    "OSField",
    "ObjectField",
    "RankFeatureField",
    "RankFeaturesField",
    "ScaledFloatField",
    "SearchAsYouTypeField",
    "ShortField",
    "TextField",
    "TimeField",
    "__version__",
]


def autodiscover():
    autodiscover_modules("documents")
