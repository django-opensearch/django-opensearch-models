from unittest import TestCase
from unittest.mock import Mock, NonCallableMock

from django.db.models.fields.files import FieldFile
from django.utils.translation import gettext_lazy as _

from django_opensearch_models.exceptions import VariableLookupError
from django_opensearch_models.fields import (
    BooleanField,
    ByteField,
    CompletionField,
    DateField,
    DEDField,
    DoubleField,
    FileField,
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
    ShortField,
    TextField,
)


class DEDFieldTestCase(TestCase):
    def test_attr_to_path(self):
        field = DEDField(attr="field")
        self.assertEqual(field._path, ["field"])

        field = DEDField(attr="obj.field")
        self.assertEqual(field._path, ["obj", "field"])

    def test_get_value_from_instance_attr(self):
        field = DEDField(attr="attr1")
        instance = NonCallableMock(attr1="foo", attr2="bar")
        self.assertEqual(field.get_value_from_instance(instance), "foo")

    def test_get_value_from_instance_related_attr(self):
        field = DEDField(attr="related.attr1")
        instance = NonCallableMock(attr1="foo", related=NonCallableMock(attr1="bar"))
        self.assertEqual(field.get_value_from_instance(instance), "bar")

    def test_get_value_from_instance_callable(self):
        field = DEDField(attr="callable")
        instance = NonCallableMock(callable=Mock(return_value="bar"))
        self.assertEqual(field.get_value_from_instance(instance), "bar")

    def test_get_value_from_instance_related_callable(self):
        field = DEDField(attr="related.callable")
        instance = NonCallableMock(related=NonCallableMock(callable=Mock(return_value="bar"), attr1="foo"))
        self.assertEqual(field.get_value_from_instance(instance), "bar")

    def test_get_value_from_instance_with_unknown_attr(self):
        class Dummy:
            attr1 = "foo"

        field = DEDField(attr="attr2", required=True)
        self.assertRaises(VariableLookupError, field.get_value_from_instance, Dummy())

    def test_get_value_from_none(self):
        field = DEDField(attr="related.none")
        instance = NonCallableMock(attr1="foo", related=None)
        self.assertEqual(field.get_value_from_instance(instance), None)

    def test_get_value_from_lazy_object(self):
        field = DEDField(attr="translation")
        instance = NonCallableMock(translation=_("foo"))
        self.assertIsInstance(field.get_value_from_instance(instance), str)
        self.assertEqual(field.get_value_from_instance(instance), "foo")


class ObjectFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = ObjectField(
            attr="person", properties={"first_name": TextField(analyzer="foo"), "last_name": TextField()}
        )

        expected_type = "text"

        self.assertEqual(
            {
                "type": "object",
                "properties": {
                    "first_name": {"type": expected_type, "analyzer": "foo"},
                    "last_name": {"type": expected_type},
                },
            },
            field.to_dict(),
        )

    def test_get_value_from_instance(self):
        field = ObjectField(
            attr="person", properties={"first_name": TextField(analyzer="foo"), "last_name": TextField()}
        )

        instance = NonCallableMock(person=NonCallableMock(first_name="foo", last_name="bar"))

        self.assertEqual(
            field.get_value_from_instance(instance),
            {
                "first_name": "foo",
                "last_name": "bar",
            },
        )

    def test_get_value_from_instance_with_partial_properties(self):
        field = ObjectField(attr="person", properties={"first_name": TextField(analyzer="foo")})

        instance = NonCallableMock(person=NonCallableMock(first_name="foo", last_name="bar"))

        self.assertEqual(field.get_value_from_instance(instance), {"first_name": "foo"})

    def test_get_value_from_instance_without_properties(self):
        field = ObjectField(attr="person")

        instance = NonCallableMock(person={"first_name": "foo", "last_name": "bar"})

        self.assertEqual(field.get_value_from_instance(instance), {"first_name": "foo", "last_name": "bar"})

    def test_get_value_from_instance_with_inner_objectfield(self):
        field = ObjectField(
            attr="person",
            properties={
                "first_name": TextField(analyzer="foo"),
                "last_name": TextField(),
                "additional": ObjectField(properties={"age": IntegerField()}),
            },
        )

        instance = NonCallableMock(
            person=NonCallableMock(first_name="foo", last_name="bar", additional=NonCallableMock(age=12))
        )

        self.assertEqual(
            field.get_value_from_instance(instance),
            {"first_name": "foo", "last_name": "bar", "additional": {"age": 12}},
        )

    def test_get_value_from_instance_with_inner_objectfield_without_properties(self):
        field = ObjectField(
            attr="person",
            properties={"first_name": TextField(analyzer="foo"), "last_name": TextField(), "additional": ObjectField()},
        )

        instance = NonCallableMock(person=NonCallableMock(first_name="foo", last_name="bar", additional={"age": 12}))

        self.assertEqual(
            field.get_value_from_instance(instance),
            {"first_name": "foo", "last_name": "bar", "additional": {"age": 12}},
        )

    def test_get_value_from_instance_with_none_inner_objectfield(self):
        field = ObjectField(
            attr="person",
            properties={
                "first_name": TextField(analyzer="foo"),
                "last_name": TextField(),
                "additional": ObjectField(properties={"age": IntegerField()}),
            },
        )

        instance = NonCallableMock(person=NonCallableMock(first_name="foo", last_name="bar", additional=None))

        self.assertEqual(
            field.get_value_from_instance(instance), {"first_name": "foo", "last_name": "bar", "additional": {}}
        )

    def test_get_value_from_iterable(self):
        field = ObjectField(
            attr="person", properties={"first_name": TextField(analyzer="foo"), "last_name": TextField()}
        )

        instance = NonCallableMock(
            person=[
                NonCallableMock(first_name="foo1", last_name="bar1"),
                NonCallableMock(first_name="foo2", last_name="bar2"),
            ]
        )

        self.assertEqual(
            field.get_value_from_instance(instance),
            [
                {
                    "first_name": "foo1",
                    "last_name": "bar1",
                },
                {
                    "first_name": "foo2",
                    "last_name": "bar2",
                },
            ],
        )

    def test_get_value_from_iterable_without_properties(self):
        field = ObjectField(attr="person")

        instance = NonCallableMock(
            person=[{"first_name": "foo1", "last_name": "bar1"}, {"first_name": "foo2", "last_name": "bar2"}]
        )

        self.assertEqual(
            field.get_value_from_instance(instance),
            [
                {
                    "first_name": "foo1",
                    "last_name": "bar1",
                },
                {
                    "first_name": "foo2",
                    "last_name": "bar2",
                },
            ],
        )


class NestedFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = NestedField(
            attr="person", properties={"first_name": TextField(analyzer="foo"), "last_name": TextField()}
        )

        expected_type = "text"

        self.assertEqual(
            {
                "type": "nested",
                "properties": {
                    "first_name": {"type": expected_type, "analyzer": "foo"},
                    "last_name": {"type": expected_type},
                },
            },
            field.to_dict(),
        )


class BooleanFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = BooleanField()

        self.assertEqual(
            {
                "type": "boolean",
            },
            field.to_dict(),
        )


class DateFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = DateField()

        self.assertEqual(
            {
                "type": "date",
            },
            field.to_dict(),
        )


class CompletionFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = CompletionField()

        self.assertEqual(
            {
                "type": "completion",
            },
            field.to_dict(),
        )


class GeoPointFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = GeoPointField()

        self.assertEqual(
            {
                "type": "geo_point",
            },
            field.to_dict(),
        )


class GeoShapeFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = GeoShapeField()

        self.assertEqual({"type": "geo_shape"}, field.to_dict())


class ByteFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = ByteField()

        self.assertEqual(
            {
                "type": "byte",
            },
            field.to_dict(),
        )


class LongFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = LongField()

        self.assertEqual(
            {
                "type": "long",
            },
            field.to_dict(),
        )


class DoubleFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = DoubleField()

        self.assertEqual(
            {
                "type": "double",
            },
            field.to_dict(),
        )


class FloatFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = FloatField()

        self.assertEqual(
            {
                "type": "float",
            },
            field.to_dict(),
        )


class ScaledFloatFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = ScaledFloatField(scaling_factor=100)

        self.assertEqual(
            {
                "type": "scaled_float",
                "scaling_factor": 100,
            },
            field.to_dict(),
        )


class IpFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = IpField()

        self.assertEqual(
            {
                "type": "ip",
            },
            field.to_dict(),
        )


class ListFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = ListField(IntegerField(attr="foo.bar"))
        self.assertEqual(
            {
                "type": "integer",
            },
            field.to_dict(),
        )

    def test_get_value_from_instance(self):
        instance = NonCallableMock(foo=NonCallableMock(bar=["alpha", "beta", "gamma"]))
        field = ListField(TextField(attr="foo.bar"))
        self.assertEqual(field.get_value_from_instance(instance), instance.foo.bar)


class ShortFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = ShortField()

        self.assertEqual(
            {
                "type": "short",
            },
            field.to_dict(),
        )


class FileFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = FileField()

        expected_type = "text"

        self.assertEqual(
            {
                "type": expected_type,
            },
            field.to_dict(),
        )

    def test_get_value_from_instance(self):
        field = FileField(attr="file")

        instance = NonCallableMock(
            file=NonCallableMock(spec=FieldFile, url="myfile.pdf"),
        )
        self.assertEqual(field.get_value_from_instance(instance), "myfile.pdf")

        field = FileField(attr="related.attr1")
        instance = NonCallableMock(attr1="foo", related=NonCallableMock(attr1="bar"))
        self.assertEqual(field.get_value_from_instance(instance), "bar")


class TextFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = TextField()

        expected_type = "text"

        self.assertEqual(
            {
                "type": expected_type,
            },
            field.to_dict(),
        )


class KeywordFieldTestCase(TestCase):
    def test_get_mapping(self):
        field = KeywordField()

        self.assertEqual(
            {
                "type": "keyword",
            },
            field.to_dict(),
        )
