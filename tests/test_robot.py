"""Testes das funcoes puras do gerador."""

import string

import pytest

from robot_rest.robot_rest import (
    PLACEHOLDERS,
    SECRET_KEY_LENGTH,
    build_context,
    generate_secret_key,
    render_project_templates,
    render_template,
    substitute_line,
)

CONTEXT = {
    "@projeto@": "myproject",
    "@HOST@": "10.0.0.1",
    "@USER@": "dbuser",
    "@PASSWORD@": "s3cr3t",
    "@NAME@": "mydb",
    "@SECRET@": "x" * SECRET_KEY_LENGTH,
}


class TestSecretKey:
    def test_has_requested_length(self):
        assert len(generate_secret_key()) == SECRET_KEY_LENGTH
        assert len(generate_secret_key(12)) == 12

    def test_uses_only_alphanumerics(self):
        allowed = set(string.ascii_letters + string.digits)
        assert set(generate_secret_key(500)) <= allowed

    def test_keys_are_not_repeated(self):
        assert generate_secret_key() != generate_secret_key()


class TestBuildContext:
    def test_covers_every_known_placeholder(self):
        context = build_context("proj", "host", "user", "pass", "name")
        assert set(context) == set(PLACEHOLDERS)

    def test_maps_arguments_to_placeholders(self):
        context = build_context("proj", "host", "user", "pass", "name")
        assert context["@projeto@"] == "proj"
        assert context["@HOST@"] == "host"
        assert context["@USER@"] == "user"
        assert context["@PASSWORD@"] == "pass"
        assert context["@NAME@"] == "name"
        assert len(context["@SECRET@"]) == SECRET_KEY_LENGTH


class TestSubstituteLine:
    def test_replaces_single_placeholder(self):
        assert substitute_line("ROOT_URLCONF = '@projeto@.urls'", CONTEXT) == (
            "ROOT_URLCONF = 'myproject.urls'"
        )

    def test_replaces_every_placeholder_on_the_same_line(self):
        # A versao antiga usava uma cadeia if/elif e trocava so o primeiro.
        line = "'USER': '@USER@', 'PASSWORD': '@PASSWORD@', 'NAME': '@NAME@'"
        assert substitute_line(line, CONTEXT) == "'USER': 'dbuser', 'PASSWORD': 's3cr3t', 'NAME': 'mydb'"

    def test_leaves_untouched_lines_alone(self):
        assert substitute_line("DEBUG = True\n", CONTEXT) == "DEBUG = True\n"

    def test_replaces_repeated_placeholder(self):
        assert substitute_line("@projeto@/@projeto@", CONTEXT) == "myproject/myproject"


class TestRenderTemplate:
    def test_writes_substituted_file(self, tmp_path):
        source = tmp_path / "in.tpl"
        source.write_text("name = '@projeto@'\nhost = '@HOST@'\n", encoding="utf-8")
        destination = tmp_path / "out.py"

        render_template(source, destination, CONTEXT)

        assert destination.read_text(encoding="utf-8") == "name = 'myproject'\nhost = '10.0.0.1'\n"

    def test_creates_missing_parent_directories(self, tmp_path):
        source = tmp_path / "in.tpl"
        source.write_text("x = '@projeto@'\n", encoding="utf-8")
        destination = tmp_path / "deep" / "nested" / "out.py"

        render_template(source, destination, CONTEXT)

        assert destination.exists()


class TestRenderProjectTemplates:
    @pytest.fixture
    def project(self, tmp_path):
        (tmp_path / "settings").mkdir()
        (tmp_path / "settings" / "dev.tpl").write_text("NAME = '@NAME@'\n", encoding="utf-8")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "settingstest.tpl").write_text(
            "from @projeto@.settings.tests import *\n", encoding="utf-8"
        )
        return tmp_path

    def test_renders_and_removes_templates(self, project):
        render_project_templates(project, CONTEXT, ["settings/dev", "tests/settingstest"])

        assert (project / "settings" / "dev.py").read_text(encoding="utf-8") == "NAME = 'mydb'\n"
        assert not (project / "settings" / "dev.tpl").exists()
        assert not (project / "tests" / "settingstest.tpl").exists()

    def test_tolerates_leading_slash_in_path(self, project):
        # A lista original misturava 'settings/dev' e '/settings/dev'; com
        # pathlib um caminho absoluto escaparia do diretorio do projeto.
        render_project_templates(project, CONTEXT, ["/settings/dev"])

        assert (project / "settings" / "dev.py").exists()
