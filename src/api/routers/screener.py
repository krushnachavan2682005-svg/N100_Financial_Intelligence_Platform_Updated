from fastapi import APIRouter

router = APIRouter()

@router.get("/screener")
def get_screener():
    return {"message": "screener route"}
