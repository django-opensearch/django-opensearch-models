from types import MethodType

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.fields.files import FieldFile
from django.utils.encoding import force_str
from django.utils.functional import Promise
from opensearchpy import (
    Boolean,
    Byte,
    Completion,
    Date,
    DateRange,
    Double,
    DoubleRange,
    Field,
    Float,
    FloatRange,
    GeoPoint,
    GeoShape,
    Integer,
    IntegerRange,
    Ip,
    IpRange,
    Keyword,
    KnnVector,
    Long,
    LongRange,
    Nested,
    Object,
    RankFeature,
    RankFeatures,
    ScaledFloat,
    SearchAsYouType,
    Short,
    Text,
)

from .exceptions import VariableLookupError


class OSField(Field):
    def __init__(self, attr=None, **kwargs):
        super().__init__(**kwargs)
        self._path = attr.split(".") if attr else []

    def __setattr__(self, key, value):
        if key == "get_value_from_instance":
            self.__dict__[key] = value
        else:
            super().__setattr__(key, value)

    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        """Given a model instance being indexed, return the value that should be sent to OpenSearch for this field."""
        if not instance:
            return None

        for attr in self._path:
            try:
                instance = instance[attr]
            except (TypeError, AttributeError, KeyError, ValueError, IndexError):
                try:
                    instance = getattr(instance, attr)
                except ObjectDoesNotExist:
                    return None
                # An AttributeError is ambiguous -- the attribute may be absent, or a property body
                # may have raised one -- and both are treated as a failed lookup, falling through to
                # the sequence-index attempt below. A TypeError is not ambiguous: `attr` is always a
                # string here, so it can only have escaped the body of a property or descriptor, and
                # it propagates instead of being recorded as a missing value.
                except AttributeError:
                    try:
                        instance = instance[int(attr)]
                    except (IndexError, ValueError, KeyError, TypeError) as e:
                        if self._required:
                            msg = f"Failed lookup for key [{attr}] in {instance!r}"
                            raise VariableLookupError(msg) from e
                        return None

            if isinstance(instance, models.manager.Manager):
                instance = instance.all()
            elif callable(instance):
                instance = instance()
            elif instance is None:
                return None

        if instance == field_value_to_ignore:
            return None

        # convert lazy object like lazy translations to string
        if isinstance(instance, Promise):
            return force_str(instance)

        return instance


class ObjectField(OSField, Object):
    def _get_inner_field_data(self, obj, field_value_to_ignore=None):
        data = {}

        # Both declaration styles end up with a `_doc_class` -- `properties={...}` has one generated
        # for it, `doc_class=SomeInnerDoc` keeps the class it was given -- so its mapping is the one
        # place the inner fields are read from.
        doc_instance = self._doc_class()
        for name, field in self._doc_class._doc_type.mapping.properties._params.get("properties", {}).items():
            if not isinstance(field, OSField):
                continue

            if field._path == []:
                field._path = [name]

            # This allows for retrieving data from an InnerDoc with prepare_field_name functions.
            prep_func = getattr(doc_instance, f"prepare_{name}", None)

            if prep_func:
                data[name] = prep_func(obj)
            else:
                data[name] = field.get_value_from_instance(obj, field_value_to_ignore)

        # This allows for ObjectFields to be indexed from dicts with
        # dynamic keys (i.e. keys/fields not defined in 'properties')
        if not data and obj and isinstance(obj, dict):
            data = obj

        return data

    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        objs = super().get_value_from_instance(instance, field_value_to_ignore)

        if objs is None:
            return {}
        try:
            is_iterable = bool(iter(objs))
        except TypeError:
            is_iterable = False

        # While dicts are iterable, they need to be excluded here so
        # their full data is indexed
        if is_iterable and not isinstance(objs, dict):
            return [
                self._get_inner_field_data(obj, field_value_to_ignore) for obj in objs if obj != field_value_to_ignore
            ]

        return self._get_inner_field_data(objs, field_value_to_ignore)


def ListField(field):
    """Wrap a field so that when get_value_from_instance is called, the field's values are iterated over."""
    original_get_value_from_instance = field.get_value_from_instance

    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        if not original_get_value_from_instance(instance):
            return []
        return list(original_get_value_from_instance(instance))

    field.get_value_from_instance = MethodType(get_value_from_instance, field)
    return field


class BooleanField(OSField, Boolean):
    pass


class ByteField(OSField, Byte):
    pass


class CompletionField(OSField, Completion):
    pass


class DateField(OSField, Date):
    pass


class DoubleField(OSField, Double):
    pass


class FloatField(OSField, Float):
    pass


class ScaledFloatField(OSField, ScaledFloat):
    pass


class GeoPointField(OSField, GeoPoint):
    pass


class GeoShapeField(OSField, GeoShape):
    pass


class IntegerField(OSField, Integer):
    pass


class IpField(OSField, Ip):
    pass


class LongField(OSField, Long):
    pass


class NestedField(Nested, ObjectField):
    pass


class ShortField(OSField, Short):
    pass


class KeywordField(OSField, Keyword):
    pass


class TextField(OSField, Text):
    pass


class SearchAsYouTypeField(OSField, SearchAsYouType):
    pass


class FileFieldMixin:
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        file_ = super().get_value_from_instance(instance, field_value_to_ignore)

        if isinstance(file_, FieldFile):
            return file_.url if file_ else ""
        return file_ or ""


class FileField(FileFieldMixin, OSField, Text):
    pass


class TimeField(KeywordField):
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        time = super().get_value_from_instance(instance, field_value_to_ignore)

        if time:
            return time.isoformat()
        return None


class KnnVectorField(OSField, KnnVector):
    """
    A dense vector for k-NN search.

    ``dimension`` is required and fixes the length of every vector in the field.

    The index must also be created with the ``knn`` setting enabled. Nothing enforces that when the
    index is built: OpenSearch accepts the mapping and indexes documents into it either way, and only
    a k-NN query fails, with ``Field '<name>' is not built for ANN search``.
    """


class RankFeatureField(OSField, RankFeature):
    pass


class RankFeaturesField(OSField, RankFeatures):
    pass


class IntegerRangeField(OSField, IntegerRange):
    pass


class FloatRangeField(OSField, FloatRange):
    pass


class LongRangeField(OSField, LongRange):
    pass


class DoubleRangeField(OSField, DoubleRange):
    pass


class DateRangeField(OSField, DateRange):
    pass


class IpRangeField(OSField, IpRange):
    pass
