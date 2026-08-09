# Contributing

Thanks for wanting to help. Bug reports, ideas and pull requests are all
welcome.

## Setting up

```bash
git clone https://github.com/AlexandreProenca/django-auto-rest-project
cd django-auto-rest-project
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running the checks

```bash
python -m pytest
```

```bash
ruff check . && ruff format --check .
```

The test suite needs no database server: it drives Django's `inspectdb`
against SQLite fixtures it builds itself.

### Against real databases

The integration tests skip unless a database is reachable. To run them:

```bash
docker compose up -d --wait
docker compose run --rm tests
docker compose down -v
```

`docker compose run --rm tests` runs the whole suite *inside* a container, on
the same network as the databases. That is the only way the MySQL path gets
exercised on most machines, because `mysqlclient` needs MySQL's C client
library and will not build without it.

To run them from your own shell instead, point the env vars at the published
ports:

```bash
ROBOT_REST_TEST_MYSQL=1 ROBOT_REST_TEST_POSTGRES=1 python -m pytest
```

### Trying changes by hand

There is a separate demo database, behind a compose profile, with a fuller
schema and real data:

```bash
docker compose --profile demo up -d --wait mysql-demo
robot_rest -ip 127.0.0.1 -port 13307 -user demo -database loja -project lojaapi
```

Keep it separate from the test fixture. The integration tests assert on the
exact models the test database produces, so enriching
`docker/initdb/mysql.sql` breaks them; put new sample data in
`docker/initdb/demo-mysql.sql` instead.

## How the project is laid out

`robot_rest` is a code generator, not a Django app.

| Module | Responsibility |
|---|---|
| `cli.py` | argument parsing, password resolution, output |
| `config.py` | configuration objects and input validation |
| `introspect.py` | `inspectdb` in-process, table filtering, model discovery |
| `render.py` | Jinja2 environment |
| `project.py` | the generation pipeline |

Templates live in `robot_rest/templates/`. Adding one takes two coordinated
edits: create the `.j2` file, then register it in `PROJECT_TEMPLATES` or
`CORE_TEMPLATES` in `project.py`. `tests/test_packaging.py` enforces both
directions, because a template missing from the distribution only fails after
`pip install` — never in a source checkout.

## Changing generated code

`tests/golden/` holds the expected output of the `core/` templates. If you
change one on purpose, regenerate the reference and read the diff before
committing:

```bash
python -m pytest tests/test_golden.py --update-golden
```

## Pull requests

- Keep the test suite and the linter green.
- Add a test for behaviour you change. If you are fixing a bug, a test that
  fails before your fix is the most useful thing in the PR.
- Note user-visible changes in `CHANGELOG.md` under "unreleased".
- Comments and docstrings in this codebase are in Brazilian Portuguese.
  Match the file you are editing.
