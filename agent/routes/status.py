import json
import os
import traceback
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import agent.config as config
from agent.models.commitment_manifest import Output, Permission, ThreadSafeCommitmentManifest

router = APIRouter(prefix=config.STATUS_API_PATH, tags=["Status"])


@router.get("/")
async def status(request: Request):
    try:

        # (TODO: currently I check for the defined output file,
        # could also check if wasm is still running if we store the process as state)
        missing_files = []
        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(
            request.app.state, 'commitment_manifest', None)
        if thread_safe_commitment_manifest == None or thread_safe_commitment_manifest.commitment_data == None:
            data = {
                "all_result_available": False,
                "commitment_manifest_locked": False
            }
        else:
            output_permissions: List[Permission] = thread_safe_commitment_manifest.commitment_data.permissions
            
            for permission in output_permissions:
                for output in permission.output:
                    print(os.path.join(config.WASM_OUTPUT_DIR, output.name))
                    if not os.path.exists(os.path.join(config.WASM_OUTPUT_DIR, output.name)):
                        missing_files.append(output.name)
            data = {
                "all_result_available": True if not missing_files else False,
                "commitment_manifest_locked": True
            }


        

        return JSONResponse(content=data, status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")
