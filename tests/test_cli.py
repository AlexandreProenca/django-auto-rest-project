"""Testes da interface de linha de comando."""

import pytest

from robot_rest.cli import PASSWORD_ENV_VAR, build_config, build_parser, resolve_password

BASE_ARGS = ["-ip", "10.0.0.1", "-user", "appuser", "-database", "appdb", "-project", "myapi"]


class TestParser:
    def test_password_is_no_longer_required(self):
        # Antes -password era obrigatorio, o que forcava a senha para o argv.
        args = build_parser().parse_args(BASE_ARGS)
        assert args.database_password is None

    def test_parses_connection_arguments(self):
        args = build_parser().parse_args(BASE_ARGS)
        assert args.database_host == "10.0.0.1"
        assert args.database_user == "appuser"
        assert args.database_name == "appdb"
        assert args.project_name == "myapi"

    @pytest.mark.parametrize("missing", ["-database", "-project"])
    def test_always_required_arguments_are_enforced(self, missing):
        index = BASE_ARGS.index(missing)
        argv = BASE_ARGS[:index] + BASE_ARGS[index + 2 :]
        with pytest.raises(SystemExit):
            build_parser().parse_args(argv)

    @pytest.mark.parametrize("optional", ["-ip", "-user"])
    def test_host_and_user_are_conditionally_required(self, optional):
        # Argparse nao pode exigi-los: sqlite nao usa nem host nem usuario.
        # A obrigatoriedade por engine vive em validate_database_config.
        index = BASE_ARGS.index(optional)
        argv = BASE_ARGS[:index] + BASE_ARGS[index + 2 :]
        assert build_parser().parse_args(argv) is not None


class TestResolvePassword:
    def test_explicit_argument_wins(self):
        assert resolve_password("fromargv", environ={PASSWORD_ENV_VAR: "fromenv"}) == "fromargv"

    def test_falls_back_to_environment(self):
        assert resolve_password(None, environ={PASSWORD_ENV_VAR: "fromenv"}) == "fromenv"

    def test_prompts_when_nothing_else_is_available(self):
        calls = []

        def fake_prompt(message):
            calls.append(message)
            return "typed"

        assert resolve_password(None, environ={}, prompt=fake_prompt) == "typed"
        assert len(calls) == 1

    def test_empty_password_from_argv_is_respected(self):
        # Bancos de desenvolvimento sem senha nao devem virar prompt.
        assert resolve_password("", environ={PASSWORD_ENV_VAR: "x"}) == ""

    def test_empty_environment_value_is_respected(self):
        assert resolve_password(None, environ={PASSWORD_ENV_VAR: ""}) == ""


class TestBuildConfig:
    def test_maps_arguments_into_config(self):
        args = build_parser().parse_args(BASE_ARGS)
        config = build_config(args, "s3cr3t")
        assert config.project_name == "myapi"
        assert config.database.as_django_dict()["PASSWORD"] == "s3cr3t"
        assert config.database.as_django_dict()["HOST"] == "10.0.0.1"

    def test_default_port_is_applied(self):
        args = build_parser().parse_args(BASE_ARGS)
        assert build_config(args, "p").database.as_django_dict()["PORT"] == "3306"

    def test_port_override(self):
        args = build_parser().parse_args([*BASE_ARGS, "-port", "3307"])
        assert build_config(args, "p").database.as_django_dict()["PORT"] == "3307"


class TestMainErrorHandling:
    def test_invalid_project_name_exits_nonzero(self, capsys):
        from robot_rest.cli import main

        argv = ["-ip", "h", "-user", "u", "-database", "d", "-project", "my-api", "-password", "p"]
        assert main(argv) == 1
        assert "erro:" in capsys.readouterr().err
