import json
from fastapi import APIRouter, HTTPException, Request, Response, Query

router = APIRouter(prefix="/v1/application", tags=["Application"])

# TODO:
# Check if manifest is expected according to lock
# Read manifest, data or unlock for binary?
# Decrypt binary

@router.post("/")
async def application(request: Request):
    try:
        data = await request.json()

        return Response(status_code=200)

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

# TODO:
# Check if user id is valid
# Check if user with user id should get result (from lock)
# If yes, provide result. (possibly sign with key for provenance?)

@router.get("/result")
async def result(user_identification: str = Query(...)):
    try:
        #TODO: Check user id and return result (if it exists)

        return Response(status_code=200, content="{result: something}", media_type="application/json")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")