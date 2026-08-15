from fastapi import APIRouter

router = APIRouter()

@router.get("/valuation")
def get_valuation():
    return {"message": "valuation route"}
