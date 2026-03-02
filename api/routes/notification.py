from services.notification_service import notification_generator,notification_queue,EventSourceResponse
from fastapi import APIRouter
from datetime import datetime,timezone

router=APIRouter(tags=["Notifications"])

@router.get('/notifications')
async def notification_event():
    return EventSourceResponse(content=notification_generator())


@router.post("/notify")
async def notify(payload: dict):
    print(id(notification_queue))
    await notification_queue.put(payload)

    return {"status": "sent"}