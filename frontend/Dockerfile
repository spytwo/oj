FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.3 /uv /uvx /bin/
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project
RUN sed -i 's/content="Flet"/content="Our Journal"/g; s/<title>Flet<\/title>/<title>Our Journal<\/title>/g' \
    /opt/venv/lib/python3.13/site-packages/flet_web/web/index.html
COPY frontend/ /app/
EXPOSE 8550
CMD ["flet", "run", "--web", "--host", "0.0.0.0", "--port", "8550", "main.py"]
