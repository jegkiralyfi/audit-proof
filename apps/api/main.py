from fastapi import FastAPI

from apps.api.routes.certificates import router as certificates_router
from apps.api.routes.health import router as health_router
from apps.api.routes.intake import router as intake_router
from apps.api.routes.jobs import router as jobs_router
from apps.api.routes.metadata import router as metadata_router
from apps.api.routes.registry import router as registry_router
from apps.api.routes.reports import router as reports_router
from apps.api.routes.verify import router as verify_router

app = FastAPI(title="Audit-Proof API", version="0.6.0a1")
app.include_router(health_router)
app.include_router(intake_router)
app.include_router(certificates_router)
app.include_router(jobs_router)
app.include_router(metadata_router)
app.include_router(registry_router)
app.include_router(reports_router)
app.include_router(verify_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8000, reload=False)
