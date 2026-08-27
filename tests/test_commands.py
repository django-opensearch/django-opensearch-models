from io import StringIO
from unittest import TestCase
from unittest.mock import DEFAULT, Mock, patch

from django.core.management import call_command
from django.core.management.base import CommandError

from django_opensearch_models import Index
from django_opensearch_models.management.commands.search_index import Command
from django_opensearch_models.registries import DocumentRegistry

from .fixtures import WithFixturesMixin


class SearchIndexTestCase(WithFixturesMixin, TestCase):
    def _mock_setup(self):
        # Mock Patch object
        patch_registry = patch("django_opensearch_models.management.commands.search_index.registry", self.registry)

        patch_registry.start()

        # Command.__init__ takes a real connection and handle() calls
        # indices.get_alias() on it, so without this the "unit" tests here
        # silently required a live OpenSearch server. Patching the factory also
        # lets the alias tests assert on the exact request that goes out.
        self.os_conn = Mock()
        self.os_conn.indices.get_alias.return_value = {}
        self.os_conn.indices.exists.return_value = False
        patch(
            "django_opensearch_models.management.commands.search_index.connections.get_connection",
            Mock(return_value=self.os_conn),
        ).start()

        methods = ["delete", "create"]
        for index in [self.index_a, self.index_b]:
            for method in methods:
                obj_patch = patch.object(index, method)
                obj_patch.start()

        self.addCleanup(patch.stopall)

    def setUp(self):
        self.out = StringIO()
        self.registry = DocumentRegistry()
        self.index_a = Index("foo")
        self.index_b = Index("bar")

        self.doc_a1_qs = Mock()
        self.doc_a1 = self._generate_doc_mock(self.ModelA, self.index_a, self.doc_a1_qs)

        self.doc_a2_qs = Mock()
        self.doc_a2 = self._generate_doc_mock(self.ModelA, self.index_a, self.doc_a2_qs)

        self.doc_b1_qs = Mock()
        self.doc_b1 = self._generate_doc_mock(self.ModelB, self.index_a, self.doc_b1_qs)

        self.doc_c1_qs = Mock()
        self.doc_c1 = self._generate_doc_mock(self.ModelC, self.index_b, self.doc_c1_qs)

        self._mock_setup()

    def test_get_models(self):
        cmd = Command()
        self.assertEqual(cmd._get_models(["foo"]), {self.ModelA, self.ModelB})

        self.assertEqual(cmd._get_models(["foo", "bar.ModelC"]), {self.ModelA, self.ModelB, self.ModelC})

        self.assertEqual(cmd._get_models([]), {self.ModelA, self.ModelB, self.ModelC})
        with self.assertRaises(CommandError):
            cmd._get_models(["unknown"])

    def test_no_action_error(self):
        cmd = Command()
        with self.assertRaises(CommandError):
            cmd.handle(action="")

    def test_delete_foo_index(self):
        with patch("django_opensearch_models.management.commands.search_index.input", Mock(return_value="y")):
            call_command("search_index", stdout=self.out, action="delete", models=["foo"])
            self.index_a.delete.assert_called_once()
            self.assertFalse(self.index_b.delete.called)

    def test_force_delete_all_indices(self):
        call_command("search_index", stdout=self.out, action="delete", force=True)
        self.index_a.delete.assert_called_once()
        self.index_b.delete.assert_called_once()

    def test_force_delete_bar_model_c_index(self):
        call_command("search_index", stdout=self.out, models=[self.ModelC._meta.label], action="delete", force=True)
        self.index_b.delete.assert_called_once()
        self.assertFalse(self.index_a.delete.called)

    def test_create_all_indices(self):
        call_command("search_index", stdout=self.out, action="create")
        self.index_a.create.assert_called_once()
        self.index_b.create.assert_called_once()

    def test_populate_all_doc_type(self):
        call_command("search_index", stdout=self.out, action="populate")
        expected_kwargs = {"parallel": False, "refresh": None}
        # One call for "Indexing NNN documents", one for indexing itself (via get_index_queryset).
        self.assertEqual(self.doc_a1.get_queryset.call_count, 2)
        self.doc_a1.update.assert_called_once_with(self.doc_a1_qs.iterator(), **expected_kwargs)
        self.assertEqual(self.doc_a2.get_queryset.call_count, 2)
        self.doc_a2.update.assert_called_once_with(self.doc_a2_qs.iterator(), **expected_kwargs)
        self.assertEqual(self.doc_b1.get_queryset.call_count, 2)
        self.doc_b1.update.assert_called_once_with(self.doc_b1_qs.iterator(), **expected_kwargs)
        self.assertEqual(self.doc_c1.get_queryset.call_count, 2)
        self.doc_c1.update.assert_called_once_with(self.doc_c1_qs.iterator(), **expected_kwargs)

    def test_populate_all_doc_type_refresh(self):
        call_command("search_index", stdout=self.out, action="populate", refresh=True)
        expected_kwargs = {"parallel": False, "refresh": True}
        self.doc_a1.update.assert_called_once_with(self.doc_a1_qs.iterator(), **expected_kwargs)
        self.doc_a2.update.assert_called_once_with(self.doc_a2_qs.iterator(), **expected_kwargs)
        self.doc_b1.update.assert_called_once_with(self.doc_b1_qs.iterator(), **expected_kwargs)
        self.doc_c1.update.assert_called_once_with(self.doc_c1_qs.iterator(), **expected_kwargs)

    def test_rebuild_indices(self):
        with patch.multiple(Command, _create=DEFAULT, _delete=DEFAULT, _populate=DEFAULT) as handles:
            handles["_delete"].return_value = True
            call_command("search_index", stdout=self.out, action="rebuild")
            handles["_delete"].assert_called()
            handles["_create"].assert_called()
            handles["_populate"].assert_called()

    def test_rebuild_indices_aborted(self):
        with patch.multiple(Command, _create=DEFAULT, _delete=DEFAULT, _populate=DEFAULT) as handles:
            handles["_delete"].return_value = False
            call_command("search_index", stdout=self.out, action="rebuild")
            handles["_delete"].assert_called()
            handles["_create"].assert_not_called()
            handles["_populate"].assert_not_called()


class AliasWireFormatTestCase(WithFixturesMixin, TestCase):
    """
    Assert the wire format of every alias request.

    `indices.update_aliases` is generated as `(self, *, body, params=None, headers=None)` with no
    **kwargs, so the @query_params wrapper has nowhere to forward an `actions` keyword and calling
    it that way raises TypeError. Every alias operation must therefore pass `body=`.

    These assert the *shape* of the outgoing request rather than that a call happened: a test
    checking only "update_aliases was called" passes just as happily against a call that would
    raise.
    """

    def setUp(self):
        self.out = StringIO()
        self.registry = DocumentRegistry()
        self.index_a = Index("foo")

        self.doc_a1_qs = Mock()
        self.doc_a1 = self._generate_doc_mock(self.ModelA, self.index_a, self.doc_a1_qs)

        patch("django_opensearch_models.management.commands.search_index.registry", self.registry).start()
        for method in ("delete", "create"):
            patch.object(self.index_a, method).start()

        self.os_conn = Mock()
        self.os_conn.indices.get_alias.return_value = {}
        self.os_conn.indices.exists.return_value = False
        patch(
            "django_opensearch_models.management.commands.search_index.connections.get_connection",
            Mock(return_value=self.os_conn),
        ).start()

        self.addCleanup(patch.stopall)

    def assert_body_only(self, call):
        """update_aliases takes a keyword-only `body`; anything else is a TypeError."""
        self.assertEqual(call.args, (), "update_aliases takes no positional arguments")
        self.assertIn("body", call.kwargs)
        self.assertNotIn("actions", call.kwargs, "`actions` is not a parameter of update_aliases")
        return call.kwargs["body"]

    def test_rebuild_with_alias_adds_the_alias(self):
        call_command("search_index", stdout=self.out, action="rebuild", use_alias=True, force=True)

        self.os_conn.indices.update_aliases.assert_called_once()
        body = self.assert_body_only(self.os_conn.indices.update_aliases.call_args)
        self.assertEqual(body["actions"][0]["add"]["alias"], "foo")

    def test_rebuild_with_alias_removes_the_conflicting_index(self):
        # An index already occupies the alias name, so it has to be removed in
        # the same atomic action as the alias being added.
        self.os_conn.indices.exists.return_value = True

        call_command("search_index", stdout=self.out, action="rebuild", use_alias=True, force=True)

        body = self.assert_body_only(self.os_conn.indices.update_aliases.call_args)
        self.assertEqual(body["actions"][1], {"remove_index": {"index": "foo"}})

    def test_delete_with_alias_removes_the_indices_behind_it(self):
        self.os_conn.indices.get_alias.return_value = {"foo-20260819": {"aliases": {"foo": {}}}}

        call_command("search_index", stdout=self.out, action="delete", models=["foo"], use_alias=True, force=True)

        self.os_conn.indices.update_aliases.assert_called_once()
        body = self.assert_body_only(self.os_conn.indices.update_aliases.call_args)
        self.assertEqual(body, {"actions": [{"remove_index": {"index": "foo-20260819"}}]})
