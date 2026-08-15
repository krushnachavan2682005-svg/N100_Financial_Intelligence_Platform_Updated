from fastapi import APIRouter

router = APIRouter()

@router.get("/portfolio")
def get_portfolio():
    return {"message": "portfolio route"}
