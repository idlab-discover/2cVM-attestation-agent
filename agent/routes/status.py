import json
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/status", tags=["Status"])

@router.post("/")
async def status(request: Request):
    try:
        data = {
            # TODO: determine if result is available
            "result_available": True,
            "commitment_manifest_locked": hasattr(request.app.state, 'commitment_manifest')
        }
            
        return JSONResponse( status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")