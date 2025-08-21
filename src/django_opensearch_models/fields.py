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
    Double,
    Field,
    Float,
    GeoPoint,
    GeoShape,
    Integer,
    Ip,
    Keyword,
    Long,
    Nested,
    Object,
    ScaledFloat,
    SearchAsYouType,
    Short,
    Text,
)

from .exceptions import VariableLookupError


class DEDField(Field):
    def __init__(self, attr=None, **kwargs):
        super().__init__(**kwargs)
        self._path = attr.split(".") if attr else []

    def __setattr__(self, key, value):
        if key == "get_value_from_instance":
            self.__dict__[key] = value
        else:
            super().__setattr__(key, value)

    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        """Given an model instance to index with ES, return the value that should be put into ES for this field."""
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
                except (TypeError, AttributeError):
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


class ObjectField(DEDField, Object):
    def _get_inner_field_data(self, obj, field_value_to_ignore=None):
        data = {}

        if hasattr(self, "properties"):
            for name, field in self.properties.to_dict().items():
                if not isinstance(field, DEDField):
                    continue

                if field._path == []:
                    field._path = [name]

                data[name] = field.get_value_from_instance(obj, field_value_to_ignore)
        else:
            doc_instance = self._doc_class()
            for name, field in self._doc_class._doc_type.mapping.properties._params.get("properties", {}).items():
                if not isinstance(field, DEDField):
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


class BooleanField(DEDField, Boolean):
    pass


class ByteField(DEDField, Byte):
    pass


class CompletionField(DEDField, Completion):
    pass


class DateField(DEDField, Date):
    pass


class DoubleField(DEDField, Double):
    pass


class FloatField(DEDField, Float):
    pass


class ScaledFloatField(DEDField, ScaledFloat):
    pass


class GeoPointField(DEDField, GeoPoint):
    pass


class GeoShapeField(DEDField, GeoShape):
    pass


class IntegerField(DEDField, Integer):
    pass


class IpField(DEDField, Ip):
    pass


class LongField(DEDField, Long):
    pass


class NestedField(Nested, ObjectField):
    pass


class ShortField(DEDField, Short):
    pass


class KeywordField(DEDField, Keyword):
    pass


class TextField(DEDField, Text):
    pass


class SearchAsYouTypeField(DEDField, SearchAsYouType):
    pass


class FileFieldMixin:
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        file_ = super().get_value_from_instance(instance, field_value_to_ignore)

        if isinstance(file_, FieldFile):
            return file_.url if file_ else ""
        return file_ or ""


class FileField(FileFieldMixin, DEDField, Text):
    pass


class TimeField(KeywordField):
    def get_value_from_instance(self, instance, field_value_to_ignore=None):
        time = super().get_value_from_instance(instance, field_value_to_ignore)

        if time:
            return time.isoformat()
        return None
