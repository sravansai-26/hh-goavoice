from fastapi import APIRouter
from app.services.telemetry import get_historical_metrics

router = APIRouter()

@router.get("/")
async def get_performance():
    metrics = get_historical_metrics()
    if metrics:
        return metrics
        
    return {
        "P50": 0,
        "P70": 0,
        "P100": 0,
        "average": 0,
        "fastest": 0,
        "slowest": 0,
        "stages": {}
    }
