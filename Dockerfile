# Imagem do robot_rest.
#
#   docker build -t robot-rest .
#   docker run --rm -v "$PWD/out:/work" --user "$(id -u):$(id -g)" robot-rest \
#       -engine postgres -ip host.docker.internal -user appuser \
#       -database shopdb -project myapi
#
# O projeto gerado sai no volume montado em /work.

# --- base: dependencias de runtime compartilhadas -------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# libmariadb3 e a biblioteca cliente que o mysqlclient carrega em runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/*


# --- builder: compila o mysqlclient e instala o pacote --------------------
FROM base AS builder

# Estas so existem para compilar o mysqlclient e ficam fora da imagem final.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential libmariadb-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY pyproject.toml README.md LICENSE.rst ./
COPY robot_rest ./robot_rest

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir '.[mysql,postgres]'


# --- runtime: imagem final --------------------------------------------------
FROM base AS runtime

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Gerar projetos como root deixaria arquivos root no volume do usuario.
RUN useradd --create-home --uid 1000 robot
USER robot
WORKDIR /work

ENTRYPOINT ["robot_rest"]
CMD ["--help"]


# --- test: mesma imagem, mais as dependencias de teste e a suite ----------
FROM builder AS test

RUN /opt/venv/bin/pip install --no-cache-dir '.[dev]'
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /src
COPY tests ./tests
COPY CHANGELOG.md CONTRIBUTING.md ./

CMD ["python", "-m", "pytest", "-q"]
