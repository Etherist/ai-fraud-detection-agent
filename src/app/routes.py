"""API routes (placeholder for future extensions)."""

from fastapi import APIRouter

router = APIRouter()

# Additional routes can be added here for future enhancements
# e.g., batch analysis, webhooks, admin endpoints

@router.get("/status")
async def get_status():
    """Get current system status."""
    return {"status": "operational"}
