from typing import Optional
from queue import Queue
from threading import Thread, Lock
import time

from .base import RenderJob, RenderConfig, BaseRenderer


class RenderQueue:
    def __init__(self, renderer: BaseRenderer, max_workers: int = 1):
        self._queue: Queue = Queue()
        self._jobs: dict[str, RenderJob] = {}
        self._active_jobs: dict[str, RenderJob] = {}
        self._renderer = renderer
        self._workers: list[Thread] = []
        self._max_workers = max_workers
        self._running: bool = False
        self._lock = Lock()

    def add_job(self, project_id: str, config: RenderConfig) -> str:
        job = RenderJob(
            id=str(__import__("uuid").uuid4()),
            project_id=project_id,
            config=config,
        )
        with self._lock:
            self._jobs[job.id] = job
            self._queue.put(job.id)
        return job.id

    def get_job(self, job_id: str) -> Optional[RenderJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status in ("pending", "running"):
                job.status = "cancelled"
                if job_id in self._active_jobs:
                    self._renderer.cancel()
                return True
        return False

    def start(self):
        if self._running:
            return
        self._running = True
        for _ in range(self._max_workers):
            worker = Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)

    def stop(self):
        self._running = False
        for _ in self._workers:
            self._queue.put(None)
        self._workers.clear()

    def _worker_loop(self):
        while self._running:
            job_id = self._queue.get()
            if job_id is None:
                break
            job = self.get_job(job_id)
            if not job or job.status == "cancelled":
                continue
            with self._lock:
                self._active_jobs[job_id] = job
            try:
                job.status = "running"
                job.started_at = time.time()
                self._renderer.current_job = job
                completed_job = self._renderer.render(None, job.config)
                job.status = completed_job.status
                job.progress = completed_job.progress
                job.output_path = completed_job.output_path
                job.error = completed_job.error
                job.completed_at = time.time()
            except Exception as e:
                job.status = "failed"
                job.error = str(e)
                job.completed_at = time.time()
            finally:
                with self._lock:
                    self._active_jobs.pop(job_id, None)

    def get_queue_length(self) -> int:
        return self._queue.qsize()

    def get_active_jobs(self) -> list[RenderJob]:
        with self._lock:
            return list(self._active_jobs.values())

    def get_all_jobs(self) -> list[RenderJob]:
        with self._lock:
            return list(self._jobs.values())
