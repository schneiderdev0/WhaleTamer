import unittest

from app.modules.generate.analyzer import analyze_project_context
from app.modules.generate.local_templates import generate_local_files
from app.modules.generate.schemas import ProjectContext


class GenerateLocalTests(unittest.TestCase):
    def test_analyzer_detects_rust_and_postgres(self) -> None:
        context = ProjectContext(
            paths=["Cargo.toml", "Cargo.lock", "src/main.rs", "src/db.rs"],
            manifests={
                "Cargo.toml": """
[package]
name = "api-server"
version = "0.1.0"

[dependencies]
tokio = "1"
sqlx = { version = "0.8", features = ["postgres", "runtime-tokio-rustls"] }
""",
            },
            snippets={"src/db.rs": 'let url = std::env::var("DATABASE_URL").unwrap();'},
            entrypoints=["src/main.rs"],
            commands=[],
        )

        analysis = analyze_project_context(context)

        self.assertEqual(analysis.stack, "rust")
        self.assertEqual(analysis.package_manager, "cargo")
        self.assertTrue(any(item.name == "postgres" for item in analysis.infrastructure))

    def test_local_rust_generation_returns_dockerfile_and_compose(self) -> None:
        context = ProjectContext(
            paths=["Cargo.toml", "Cargo.lock", "src/main.rs"],
            manifests={
                "Cargo.toml": """
[package]
name = "worker-app"
version = "0.1.0"
""",
            },
            entrypoints=["src/main.rs"],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertIn("Dockerfile", rendered)
        self.assertIn("docker-compose.yaml", rendered)
        self.assertIn("worker_app", rendered["Dockerfile"])

    def test_local_fastapi_generation_includes_postgres_service(self) -> None:
        context = ProjectContext(
            paths=["pyproject.toml", "app/main.py", "app/core/settings.py"],
            manifests={
                "pyproject.toml": """
[project]
name = "sample-api"
dependencies = ["fastapi", "uvicorn", "asyncpg"]

[tool.uv]
dev-dependencies = []
""",
            },
            snippets={
                "app/core/settings.py": """
postgres_host = "postgres"
postgres_user = "postgres"
postgres_password = "postgres"
postgres_db = "app"
"""
            },
            entrypoints=["app/main.py"],
            commands=["uvicorn app.main:app --host 0.0.0.0 --port 8000"],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertIn("docker-compose.yaml", rendered)
        self.assertIn("postgres:", rendered["docker-compose.yaml"])
        self.assertIn("POSTGRES_HOST: postgres", rendered["docker-compose.yaml"])

    def test_local_go_generation_returns_dockerfile_and_compose(self) -> None:
        context = ProjectContext(
            paths=["go.mod", "go.sum", "cmd/api/main.go", "internal/handler/http.go"],
            manifests={
                "go.mod": """
module github.com/example/go-api

go 1.24

require github.com/redis/go-redis/v9 v9.7.0
""",
            },
            entrypoints=["cmd/api/main.go"],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertEqual(analysis.stack, "go")
        self.assertTrue(any(item.name == "redis" and item.confidence == "medium" for item in analysis.infrastructure))
        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertIn("Dockerfile", rendered)
        self.assertIn("docker-compose.yaml", rendered)
        self.assertIn("go_api", rendered["Dockerfile"])
        self.assertIn("./cmd/api", rendered["Dockerfile"])
        self.assertNotIn("\n  redis:\n", rendered["docker-compose.yaml"])
        self.assertIn("# - redis:", rendered["docker-compose.yaml"])

    def test_local_django_generation_returns_gunicorn_and_postgres(self) -> None:
        context = ProjectContext(
            paths=[
                "pyproject.toml",
                "manage.py",
                "config/settings.py",
                "config/wsgi.py",
            ],
            manifests={
                "pyproject.toml": """
[project]
name = "django-app"
dependencies = ["django", "gunicorn", "psycopg[binary]"]
""",
            },
            snippets={
                "config/settings.py": """
postgres_host = "postgres"
postgres_user = "postgres"
postgres_password = "postgres"
postgres_db = "app"
"""
            },
            entrypoints=["manage.py"],
            commands=[],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertEqual(analysis.stack, "django")
        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertIn("gunicorn", rendered["Dockerfile"])
        self.assertIn("config.wsgi:application", rendered["Dockerfile"])
        self.assertIn("postgres:", rendered["docker-compose.yaml"])

    def test_local_flask_generation_returns_gunicorn(self) -> None:
        context = ProjectContext(
            paths=["requirements.txt", "app.py"],
            manifests={
                "requirements.txt": """
flask==3.1.0
gunicorn==23.0.0
redis==5.2.1
""",
            },
            entrypoints=["app.py"],
            commands=[],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertEqual(analysis.stack, "flask")
        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertIn("gunicorn", rendered["Dockerfile"])
        self.assertIn("app:app", rendered["Dockerfile"])

    def test_medium_confidence_infrastructure_is_advisory_only(self) -> None:
        context = ProjectContext(
            paths=["requirements.txt", "app.py"],
            manifests={
                "requirements.txt": """
flask==3.1.0
gunicorn==23.0.0
redis==5.2.1
"""
            },
            entrypoints=["app.py"],
            commands=[],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertEqual(analysis.stack, "flask")
        self.assertTrue(any(item.name == "redis" and item.confidence == "medium" for item in analysis.infrastructure))
        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertNotIn("\n  redis:\n", rendered["docker-compose.yaml"])
        self.assertIn("# - redis:", rendered["docker-compose.yaml"])

    def test_minio_dependency_only_is_advisory_only(self) -> None:
        context = ProjectContext(
            paths=["pyproject.toml", "app/main.py"],
            manifests={
                "pyproject.toml": """
[project]
name = "object-api"
dependencies = ["fastapi", "uvicorn", "boto3"]

[tool.uv]
dev-dependencies = []
"""
            },
            entrypoints=["app/main.py"],
            commands=["uvicorn app.main:app --host 0.0.0.0 --port 8000"],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertEqual(analysis.stack, "fastapi")
        self.assertTrue(any(item.name == "minio" and item.confidence == "medium" for item in analysis.infrastructure))
        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertNotIn("\n  minio:\n", rendered["docker-compose.yaml"])
        self.assertIn("# - minio:", rendered["docker-compose.yaml"])

    def test_fullstack_monorepo_generation_returns_split_services(self) -> None:
        context = ProjectContext(
            paths=[
                "frontend/package.json",
                "frontend/package-lock.json",
                "frontend/src/main.tsx",
                "backend/pyproject.toml",
                "backend/app/main.py",
                "backend/app/core/settings.py",
            ],
            manifests={
                "frontend/package.json": """
{
  "name": "frontend-app",
  "scripts": {
    "build": "vite build",
    "start": "vite --host 0.0.0.0 --port 3000"
  },
  "dependencies": {
    "react": "^19.0.0",
    "vite": "^6.0.0"
  }
}
""",
                "backend/pyproject.toml": """
[project]
name = "backend-api"
dependencies = ["fastapi", "uvicorn", "asyncpg"]

[tool.uv]
dev-dependencies = []
""",
            },
            snippets={
                "backend/app/core/settings.py": """
postgres_host = "postgres"
postgres_user = "postgres"
postgres_password = "postgres"
postgres_db = "app"
"""
            },
            entrypoints=["frontend/src/main.tsx", "backend/app/main.py"],
            commands=["uvicorn app.main:app --host 0.0.0.0 --port 8000"],
        )

        analysis = analyze_project_context(context)
        files = generate_local_files(analysis, context)

        self.assertEqual(analysis.stack, "fullstack")
        self.assertIsNotNone(files)
        rendered = {item.path: item.content for item in files or []}
        self.assertIn("frontend/Dockerfile", rendered)
        self.assertIn("backend/Dockerfile", rendered)
        self.assertIn("docker-compose.yaml", rendered)
        self.assertIn("dockerfile: frontend/Dockerfile", rendered["docker-compose.yaml"])
        self.assertIn("dockerfile: backend/Dockerfile", rendered["docker-compose.yaml"])
        self.assertIn("  frontend:", rendered["docker-compose.yaml"])
        self.assertIn("  backend:", rendered["docker-compose.yaml"])
        self.assertIn("  postgres:", rendered["docker-compose.yaml"])


if __name__ == "__main__":
    unittest.main()
