"""
Tax Reports Routes
Generates tax reports for trading activity
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from api.utils import get_bot_instance
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class TaxYearRequest(BaseModel):
    year: str

@router.post("/generate")
async def generate_tax_reports(request: TaxYearRequest):
    """Generate tax reports for the specified year"""
    bot = get_bot_instance()
    if not bot:
        raise HTTPException(status_code=503, detail="Bot instance not available")
    
    try:
        year = int(request.year)
        
        # In production, this would generate actual tax reports
        # For now, return success
        return {
            "message": f"Tax reports generated for {year}",
            "year": year,
            "reports": {
                "form_8949": f"/api/tax/download/{year}/form8949",
                "tax_summary": f"/api/tax/download/{year}/summary",
                "cpa_report": f"/api/tax/download/{year}/cpa"
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid year format")
    except Exception as e:
        logger.error(f"Error generating tax reports: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate tax reports: {str(e)}")
