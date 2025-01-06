import json
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import agent.config as config

router = APIRouter(prefix=config.STATUS_API_PATH, tags=["Status"])

@router.post("/")
async def status(request: Request):
    try:
        
        # (TODO: check if wasm process is still running)
        
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