"""Testes dos templates que substituem o drf_gen."""

import ast

import pytest
from jinja2 import UndefinedError

from robot_rest.config import DatabaseConfig, ProjectConfig
from robot_rest.introspect import DiscoveredModel
from robot_rest.render import render

MODELS = [DiscoveredModel(name="AlbumTrack"), DiscoveredModel(name="Artist")]

CORE_TEMPLATES = [
    "core/serializers.py.j2",
    "core/views.py.j2",
    "core/urls.py.j2",
    "core/admin.py.j2",
]


@pytest.fixture
def context():
    config = ProjectConfig(project_name="myapi", database=DatabaseConfig(name="appdb"))
    return {**config.as_template_context(), "models": MODELS}


def parse(source):
    """Falha o teste se o codigo gerado nao for Python valido."""
    return ast.parse(source)


@pytest.mark.parametrize("template", CORE_TEMPLATES)
def test_generated_code_is_valid_python(template, context):
    parse(render(template, context))


@pytest.mark.parametrize("template", CORE_TEMPLATES)
def test_generated_code_is_valid_python_with_no_models(template, context):
    # Um banco vazio nao pode gerar um arquivo quebrado.
    parse(render(template, {**context, "models": []}))


class TestSerializers:
    def test_defines_one_serializer_per_model(self, context):
        tree = parse(render("core/serializers.py.j2", context))
        classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        assert classes == ["AlbumTrackSerializer", "ArtistSerializer"]

    def test_imports_every_model(self, context):
        source = render("core/serializers.py.j2", context)
        assert "AlbumTrack," in source
        assert "Artist," in source

    def test_omits_import_when_there_are_no_models(self, context):
        source = render("core/serializers.py.j2", {**context, "models": []})
        assert "from .models import" not in source


class TestViews:
    def test_defines_one_viewset_per_model(self, context):
        tree = parse(render("core/views.py.j2", context))
        classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
        assert classes == ["AlbumTrackViewSet", "ArtistViewSet"]

    def test_viewsets_are_wired_to_their_serializer(self, context):
        source = render("core/views.py.j2", context)
        assert "serializer_class = AlbumTrackSerializer" in source

    def test_querysets_are_ordered_for_stable_pagination(self, context):
        # Sem order_by, o DRF emite UnorderedObjectListWarning e as paginas
        # podem repetir ou pular registros.
        source = render("core/views.py.j2", context)
        assert 'queryset = AlbumTrack.objects.all().order_by("pk")' in source
        assert 'queryset = Artist.objects.all().order_by("pk")' in source


class TestUrls:
    def test_registers_every_model_on_the_router(self, context):
        source = render("core/urls.py.j2", context)
        assert 'router.register(r"album-track", views.AlbumTrackViewSet, basename="album_track")' in source
        assert 'router.register(r"artist", views.ArtistViewSet, basename="artist")' in source

    def test_router_is_included_in_urlpatterns(self, context):
        source = render("core/urls.py.j2", context)
        assert 'path("", include(router.urls))' in source


class TestAdmin:
    def test_registers_every_model(self, context):
        source = render("core/admin.py.j2", context)
        assert "@admin.register(AlbumTrack)" in source
        assert "@admin.register(Artist)" in source


class TestStrictUndefined:
    def test_missing_variable_fails_loudly(self):
        # Sem StrictUndefined, um typo geraria um arquivo silenciosamente vazio.
        with pytest.raises(UndefinedError):
            render("core/serializers.py.j2", {})
