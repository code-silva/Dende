# BUILDER
FROM python:3.12-slim AS builder

WORKDIR /app

# Instalando apenas o necessário para compilar pacotes
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Pegando o gerenciador de pacotes UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Criando o ambiente virtual e baixando as dependências
COPY requirements.txt .
RUN uv venv /app/.venv && \
    uv pip install --no-cache -r requirements.txt

# RUNNER
FROM python:3.12-slim AS runner

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Instalando as dependências de EXECUÇÃO
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    gdal-bin \
    spatialite-bin \
    libsqlite3-mod-spatialite \
    && rm -rf /var/lib/apt/lists/*

# Copia o .venv pronto do BUILDER
COPY --from=builder /app/.venv /app/.venv
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]