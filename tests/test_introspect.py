"""Testes da descoberta de modelos (o que substituiu o drf_gen)."""

import pytest

from robot_rest.introspect import (
    DiscoveredModel,
    IntrospectionError,
    camel_to_snake,
    discover_models,
)

INSPECTDB_OUTPUT = """\
# This is an auto-generated Django model module.
from django.db import models


class Artist(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'artist'


class AlbumTrack(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'album_track'
"""


class TestCamelToSnake:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Artist", "artist"),
            ("AlbumTrack", "album_track"),
            ("HTTPServer", "http_server"),
            ("Order2Item", "order2_item"),
            ("A", "a"),
        ],
    )
    def test_conversions(self, value, expected):
        assert camel_to_snake(value) == expected


class TestDiscoveredModel:
    def test_derives_route_and_basename(self):
        model = DiscoveredModel(name="AlbumTrack")
        assert model.snake_name == "album_track"
        assert model.route == "album-track"
        assert model.basename == "album_track"


class TestDiscoverModels:
    def test_finds_every_model(self):
        assert [m.name for m in discover_models(INSPECTDB_OUTPUT)] == ["AlbumTrack", "Artist"]

    def test_results_are_sorted_for_stable_output(self):
        # Saida estavel evita diffs ruidosos ao regerar o projeto.
        names = [m.name for m in discover_models(INSPECTDB_OUTPUT)]
        assert names == sorted(names)

    def test_captures_db_table(self):
        by_name = {m.name: m for m in discover_models(INSPECTDB_OUTPUT)}
        assert by_name["AlbumTrack"].db_table == "album_track"

    def test_ignores_nested_meta_classes(self):
        assert all(m.name != "Meta" for m in discover_models(INSPECTDB_OUTPUT))

    def test_ignores_classes_that_are_not_models(self):
        source = "class Helper:\n    pass\n\n\nclass Thing(models.Model):\n    pass\n"
        assert [m.name for m in discover_models(source)] == ["Thing"]

    def test_accepts_bare_model_base(self):
        source = "from django.db.models import Model\n\n\nclass Thing(Model):\n    pass\n"
        assert [m.name for m in discover_models(source)] == ["Thing"]

    def test_empty_schema_yields_no_models(self):
        assert discover_models("from django.db import models\n") == []

    def test_broken_source_raises_a_clear_error(self):
        with pytest.raises(IntrospectionError):
            discover_models("class Thing(models.Model)\n    oops")
