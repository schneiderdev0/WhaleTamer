import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.exeptions import setup_exeption_handler
from app.core.settings import s
from app.modules.auth.router import router as auth_router
from app.modules.collector.router import router as collector_router
from app.modules.generate.router import router as generate_router
from app.modules.reports.router import router as reports_router
from app.modules.telegram.router import router as telegram_router


def main() -> FastAPI:
    app = FastAPI()
    setup_exeption_handler(app)

    # CORS for frontend / external clients
    origins = s.backend_cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["System"])
    async def health_check():
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(generate_router)
    app.include_router(collector_router)
    app.include_router(reports_router)
    app.include_router(telegram_router)

    return app


if __name__ == "__main__":
    uvicorn.run("app.main:main", factory=True, reload=True)
