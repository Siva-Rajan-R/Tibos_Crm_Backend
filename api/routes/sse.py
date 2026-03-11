from ..dependencies.token_verification import verify_user
from fastapi import Request,APIRouter,Depends,Query,HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials,HTTPBasicCredentials
from sse_starlette.sse import EventSourceResponse
from services.sse import sse_manager,sse_msg_builder
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
    user_name=user['email'].split("@")[0]
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid auth token"
        )

    user_id=user['id']
    ic(user_id)
    data = await sse_manager.create(user_id)
    queue=data['queue']
    if data['send_greet']:
        message=sse_msg_builder(title=f"Hi, {user_name.title()}",description="Welcome to tibos crm",type="Greet")
        await sse_manager.send(client_id=user_id,data=message)

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
            await sse_manager.remove(user_id)

    return EventSourceResponse(event_generator())