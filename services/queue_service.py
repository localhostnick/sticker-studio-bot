import asyncio
from typing import Dict, Optional, Set
from utils.logger import logger


class TaskContext:
    def __init__(self, user_id: int, task_name: str):
        self.user_id = user_id
        self.task_name = task_name
        self.cancel_requested = False
        self.current_step = 0
        self.total_steps = 0
        self.status_message = "Starting..."

    def request_cancel(self) -> None:
        self.cancel_requested = True
        logger.info(f"Cancellation requested for task '{self.task_name}' (User: {self.user_id})")

    def check_cancelled(self) -> None:
        if self.cancel_requested:
            raise asyncio.CancelledError(f"Task '{self.task_name}' cancelled by user.")


class QueueService:
    _active_tasks: Dict[int, TaskContext] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def start_task(cls, user_id: int, task_name: str) -> TaskContext:
        """Registers an active task for a user. Throws error if user already has an active task."""
        async with cls._lock:
            if user_id in cls._active_tasks:
                existing = cls._active_tasks[user_id]
                raise RuntimeError(f"You already have an active process running ('{existing.task_name}'). Please wait or send /cancel.")
            
            ctx = TaskContext(user_id, task_name)
            cls._active_tasks[user_id] = ctx
            return ctx

    @classmethod
    async def finish_task(cls, user_id: int) -> None:
        """Removes user's active task from queue."""
        async with cls._lock:
            if user_id in cls._active_tasks:
                del cls._active_tasks[user_id]

    @classmethod
    async def cancel_user_task(cls, user_id: int) -> bool:
        """Requests cancellation of active user task."""
        async with cls._lock:
            if user_id in cls._active_tasks:
                cls._active_tasks[user_id].request_cancel()
                return True
            return False

    @classmethod
    async def get_active_task(cls, user_id: int) -> Optional[TaskContext]:
        """Gets user's active task context if present."""
        async with cls._lock:
            return cls._active_tasks.get(user_id)
