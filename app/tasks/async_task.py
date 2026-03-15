import asyncio
from celery import Task


class AsyncTask(Task):
    """
    Base Celery task that allows running async code.
    Each task execution gets its own event loop.
    """

    def run_async(self, coro):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
