FROM python:3.14-slim-bookworm
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync
COPY . .
EXPOSE 8000
CMD ["/app/.venv/bin/uvicorn", "app.main:main", "--factory", "--host", "0.0.0.0", "--port", "8000"]