from __future__ import annotations

import asyncio
import logging
import traceback
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy.orm import Session

from app.config.settings import settings
from app.infra.db.models.task import Task
from app.infra.db.session import SessionLocal

logger = logging.getLogger(__name__)


class TaskQueue:
    """In-process async task executor.

    For MVP: uses ThreadPoolExecutor for CPU/IO work and asyncio for
    async workflows. Replaceable with Celery/Redis later via the same
    interface.
    """

    def __init__(self, max_workers: int | None = None) -> None:
        if max_workers is None:
            max_workers = settings.max_queue_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._running: dict[int, asyncio.Task[Any]] = {}

    def submit(
        self,
        task_record: Task,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Submit a synchronous function for background execution.

        The function receives the Task record as its first argument
        and is responsible for updating the Task status.
        """
        self._executor.submit(self._run_sync, task_record, fn, *args, **kwargs)

    def submit_async(
        self,
        task_record: Task,
        coro_fn: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Submit an async coroutine for background execution."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        async_task = loop.create_task(
            self._run_async(task_record, coro_fn, *args, **kwargs)
        )
        self._running[task_record.id] = async_task

    def _run_sync(
        self,
        task_record: Task,
        fn: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Run a sync function and update task status on completion/failure."""
        db: Session = SessionLocal()
        try:
            # Re-attach task to this session
            task = db.get(Task, task_record.id)
            if task:
                task.status = 'running'
                db.commit()

            fn(*args, **kwargs)

            if task:
                task = db.get(Task, task_record.id)
                if task and task.status == 'running':
                    task.status = 'success'
                    db.commit()
        except Exception as e:
            logger.error('Task %d failed: %s', task_record.id, e)
            logger.error(traceback.format_exc())
            try:
                task = db.get(Task, task_record.id)
                if task:
                    task.status = 'failed'
                    task.error_message = str(e)[:2000]
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    async def _run_async(
        self,
        task_record: Task,
        coro_fn: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Run an async coroutine and update task status on completion/failure."""
        db: Session = SessionLocal()
        try:
            task = db.get(Task, task_record.id)
            if task:
                task.status = 'running'
                db.commit()

            await coro_fn(*args, **kwargs)

            task = db.get(Task, task_record.id)
            if task and task.status == 'running':
                task.status = 'success'
                db.commit()
        except Exception as e:
            logger.error('Async task %d failed: %s', task_record.id, e)
            logger.error(traceback.format_exc())
            try:
                task = db.get(Task, task_record.id)
                if task:
                    task.status = 'failed'
                    task.error_message = str(e)[:2000]
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()
            self._running.pop(task_record.id, None)


# Global singleton
_task_queue: TaskQueue | None = None


def get_task_queue() -> TaskQueue:
    """Get the global task queue singleton."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
