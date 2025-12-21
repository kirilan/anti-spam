from datetime import datetime

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.celery_app import celery_app
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.tasks.email_tasks import scan_inbox_task

router = APIRouter()


class ScanTaskRequest(BaseModel):
    days_back: int = 90
    max_emails: int = 100


class BatchRequestsTaskRequest(BaseModel):
    broker_ids: list[str]
    framework: str = "GDPR/CCPA"


class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    info: dict | None = None
    result: dict | None = None


class WorkerStatus(BaseModel):
    name: str
    status: str
    active_tasks: int
    queued_tasks: int
    scheduled_tasks: int
    total_tasks: int
    concurrency: int | None = None
    uptime: int | None = None


class TaskQueueHealth(BaseModel):
    workers_online: int
    total_active_tasks: int
    total_queued_tasks: int
    workers: list[WorkerStatus]
    last_updated: datetime


@router.post("/scan", response_model=TaskResponse)
def start_scan_task(
    request: ScanTaskRequest,
    current_user: User = Depends(get_current_user),
):
    """Start an async email scan task"""
    task = scan_inbox_task.delay(
        str(current_user.id), days_back=request.days_back, max_emails=request.max_emails
    )
    return TaskResponse(task_id=task.id, status="started")


@router.get("/health", response_model=TaskQueueHealth)
def get_task_queue_health(current_user: User = Depends(require_admin)):
    """Return basic Celery worker and queue stats"""
    inspect = celery_app.control.inspect()
    stats = inspect.stats() if inspect else None
    active = inspect.active() if inspect else None
    scheduled = inspect.scheduled() if inspect else None
    reserved = inspect.reserved() if inspect else None
    heartbeat = inspect.ping() if inspect else None

    worker_names = set()
    for data in (stats, active, scheduled, reserved):
        if isinstance(data, dict):
            worker_names.update(data.keys())

    workers: list[WorkerStatus] = []
    for name in sorted(worker_names):
        worker_stats = stats.get(name, {}) if isinstance(stats, dict) else {}
        pool_info = (
            worker_stats.get("pool", {}) if isinstance(worker_stats.get("pool"), dict) else {}
        )
        total_info = (
            worker_stats.get("total", {}) if isinstance(worker_stats.get("total"), dict) else {}
        )

        workers.append(
            WorkerStatus(
                name=name,
                status="online" if heartbeat and name in heartbeat else "offline",
                active_tasks=len(active.get(name, []))
                if isinstance(active, dict) and active.get(name)
                else 0,
                queued_tasks=len(reserved.get(name, []))
                if isinstance(reserved, dict) and reserved.get(name)
                else 0,
                scheduled_tasks=len(scheduled.get(name, []))
                if isinstance(scheduled, dict) and scheduled.get(name)
                else 0,
                total_tasks=total_info.get("tasks", 0) if isinstance(total_info, dict) else 0,
                concurrency=pool_info.get("max-concurrency")
                if isinstance(pool_info, dict)
                else None,
                uptime=worker_stats.get("uptime") if worker_stats else None,
            )
        )

    workers_online = sum(1 for worker in workers if worker.status == "online")
    total_active = sum(worker.active_tasks for worker in workers)
    total_queued = sum(worker.queued_tasks + worker.scheduled_tasks for worker in workers)

    return TaskQueueHealth(
        workers_online=workers_online,
        total_active_tasks=total_active,
        total_queued_tasks=total_queued,
        workers=workers,
        last_updated=datetime.utcnow(),
    )


@router.get("/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, current_user: User = Depends(get_current_user)):
    """Get the status of a Celery task"""
    result = AsyncResult(task_id, app=celery_app)

    response = TaskStatusResponse(task_id=task_id, state=result.status)

    if result.status == "PROGRESS":
        response.info = result.info
    elif result.status == "SUCCESS":
        response.result = result.result
    elif result.status == "FAILURE":
        response.info = {"error": str(result.result) if result.result else "Unknown error"}

    return response


@router.delete("/{task_id}")
def cancel_task(task_id: str, current_user: User = Depends(get_current_user)):
    """Cancel/revoke a running task"""
    celery_app.control.revoke(task_id, terminate=True)
    return {"task_id": task_id, "status": "cancelled"}
