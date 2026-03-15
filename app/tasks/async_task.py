import asyncio
from celery import Task


class AsyncTask(Task):
    _loop = None

    def get_loop(self):
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    def run_async(self, coro):
        loop = self.get_loop()
        return loop.run_until_complete(coro)
