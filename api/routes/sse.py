from ..dependencies.token_verification import verify_user
from fastapi import Request,APIRouter,Depends,Query,HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials,HTTPBasicCredentials
from sse_starlette.sse import EventSourceResponse
from services.sse import sse_manager
import json
from icecream import ic
from datetime import datetime,timezone

router=APIRouter(
    tags=["Server Sent Events"]
)

@router.get("/sse/stream")
async def stream_bulk(request: Request,token:str=Query(...)):
    ic(token)
    user=await verify_user(request=request,credentials=HTTPAuthorizationCredentials(scheme="Bearer",credentials=token))
    ic(user)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid auth token"
        )

    user_id=user['id']
    ic(user_id)
    queue = sse_manager.create(user_id)

    async def event_generator():
        try:
            while True:

                if await request.is_disconnected():
                    break

                data = await queue.get()
                ic(data)
                utc_datetime=datetime.now(tz=timezone.utc)
                data['datetime']=utc_datetime.isoformat()
                yield {
                    "event": "notification",
                    "data": json.dumps(data)
                }
        finally:
            sse_manager.remove(user_id)

    return EventSourceResponse(event_generator())