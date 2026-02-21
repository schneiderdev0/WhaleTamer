import uvicorn
from fastapi.applications import FastAPI

from app.core.exeptions import setup_exeption_handler
from app.modules.auth.router import router as auth_router
from app.modules.generate.router import router as generate_router


def main() -> FastAPI:
    app = FastAPI()
    setup_exeption_handler(app)

    app.include_router(auth_router)
    app.include_router(generate_router)

    return app


if __name__ == "__main__":
    uvicorn.run("app.main:main", factory=True, reload=True)
