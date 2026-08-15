from fastapi import APIRouter

router = APIRouter()


@router.get("/companies/{ticker}/documents")
def get_documents(ticker: str):
    return [
        {
            "year": 2023,
            "type": "Annual Report",
            "url": f"https://example.com/{ticker}_AR_2023.pdf",
            "is_url_valid": True,
        }
    ]
