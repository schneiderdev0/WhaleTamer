FROM python:3.14-slim-bookworm AS backend
WORKDIR /app

RUN pip install --no-cache-dir uv

COPY wt-backend/pyproject.toml wt-backend/uv.lock* ./
RUN uv sync --frozen --no-dev

COPY wt-backend/ ./

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.main:main", "--factory", "--host", "0.0.0.0", "--port", "8000"]


FROM node:22-bookworm-slim AS frontend
WORKDIR /app

RUN corepack enable

COPY frontend/package.json frontend/yarn.lock ./

RUN yarn install

COPY frontend/ ./

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN yarn build

EXPOSE 5173

CMD ["yarn", "vite", "preview", "--host", "0.0.0.0", "--port", "5173"]
