import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document

app = FastAPI(title="Cleaning Business API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Cleaning Business Backend is running"}

# Public endpoint for booking requests
class BookingPayload(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    service_type: str
    preferred_date: str
    preferred_time: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    notes: Optional[str] = None

@app.post("/api/book")
def create_booking(payload: BookingPayload):
    try:
        # Persist to database using helper (auto timestamps)
        doc = create_document("bookingrequest", payload.dict())
        return {"success": True, "message": "Booking request received!", "data": doc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health and schema endpoints for tooling
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        from database import db
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Expose schemas for admin tools/viewers
@app.get("/schema")
def get_schema():
    try:
        import schemas
        result = {}
        for name in dir(schemas):
            obj = getattr(schemas, name)
            if getattr(obj, "__module__", None) == "schemas" and hasattr(obj, "model_json_schema"):
                result[name] = obj.model_json_schema()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
