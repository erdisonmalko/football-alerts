import asyncio
from celery import Task

from app.core.logger import get_logger

logger = get_logger(__name__)


class AsyncTask(Task):
    """
    Celery Task base class that safely runs async functions.
    """

    def run_async(self, coro):
        logger.debug("[AsyncTask] Running async task %s", self.name)
        return asyncio.run(coro)
