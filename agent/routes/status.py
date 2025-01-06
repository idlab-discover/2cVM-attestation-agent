import json
import os
from typing import List

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse

import agent.config as config
from agent.models.commitment_manifest import Output, ThreadSafeCommitmentManifest

router = APIRouter(prefix=config.STATUS_API_PATH, tags=["Status"])


@router.post("/")
async def status(request: Request):
    try:

        # (TODO: currently I check for the defined output file,
        # could also check if wasm is still running if we store the process as state)

        thread_safe_commitment_manifest: ThreadSafeCommitmentManifest = getattr(
            request.app.state, 'commitment_manifest', None)
        if thread_safe_commitment_manifest != None and thread_safe_commitment_manifest.data != None:
            commitment_manifest_locked = True
        else:
            commitment_manifest_locked = False

        output_permissions: List[Output] = thread_safe_commitment_manifest.commitment_data.permissions

        results_available = all(
            os.path.exists(os.path.join(config.WASM_OUTPUT_DIR, output.name))
            for output in output_permissions
            # Only checking output files in Python, Rust prod impl might need to check other places (like shared memory?)
            if output.type == "file"
        )

        data = {
            "all_result_available": results_available,
            "commitment_manifest_locked": commitment_manifest_locked
        }

        return JSONResponse(content=data, status_code=200)

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
