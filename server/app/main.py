# server/app/main.py
# Minimal FastAPI app with health router + startup/shutdown wiring.

from fastapi import FastAPI
from .settings import Settings
from .lifecycle import on_startup, on_shutdown
from .routers import health, config, admin, csv, jobs, dummy

def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.APP_NAME)

    # lifecycle hooks
    @app.on_event("startup")
    def _startup():
        on_startup(app, settings)

    @app.on_event("shutdown")
    def _shutdown():
        on_shutdown(app)

    # routers
    app.include_router(health.router)
    app.include_router(config.router)
    app.include_router(admin.router)
    app.include_router(csv.router)
    app.include_router(jobs.router)
    app.include_router(dummy.router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = Settings()
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)