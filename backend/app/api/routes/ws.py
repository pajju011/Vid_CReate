from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.api.websocket_manager import ws_manager
from app.db.session import SessionLocal
from app.models.entities import Job

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/jobs/{job_id}")
async def job_progress_websocket(websocket: WebSocket, job_id: str):
    await ws_manager.connect(job_id, websocket)
    try:
        # Immediately push current status from database
        with SessionLocal() as session:
            job = session.query(Job).filter(Job.id == job_id).first()
            if job:
                await websocket.send_json({
                    "job_id": job.id,
                    "status": job.status,
                    "progress": job.progress,
                    "current_step": job.current_step,
                    "error_message": job.error_message,
                    "result_data": job.result_data,
                    "privacy_mode": job.privacy_mode
                })

        # Keep connection open and handle incoming client commands (e.g. heartbeat ping)
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(job_id, websocket)
    except Exception:
        ws_manager.disconnect(job_id, websocket)

