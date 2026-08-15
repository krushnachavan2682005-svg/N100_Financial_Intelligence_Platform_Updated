from fastapi import APIRouter

router = APIRouter()

@router.get("/sectors")
def get_sectors():
    return {"message": "sectors route"}
