from fastapi import APIRouter

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/")
def list_jobs() -> dict[str, list]:
    return {"jobs": []}
