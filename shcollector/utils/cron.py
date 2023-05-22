from __future__ import annotations
from typing import Callable, List, Dict, Any
from croniter import croniter
from datetime import datetime
import pytz
import sched
import time
import logging

logger = logging.getLogger('cron')
timezone = pytz.timezone('Europe/Paris')


class CronScheduler():

    def __init__(self: CronScheduler):
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.jobs: List[Job] = []
        self.started: bool = False

    def schedule(self: CronScheduler, job: Job) -> None:
        self.jobs.append(job)
        if self.started:
            self._run(job)

    def _run(self: CronScheduler, job: Job) -> None:
        run_date = job.cron.get_next(datetime)
        while run_date <= timezone.localize(datetime.now()):
            run_date = job.cron.get_next(datetime)
            logger.debug("Oops too late")
        runtime = run_date.timestamp()
        logger.debug(f"Scheduling {job.name} run at {str(run_date)}")
        kwargs = job.args.copy()
        if job.inject_run_date:
            kwargs['run_date'] = run_date
        self.scheduler.enterabs(runtime, job.priority, job.call, kwargs=kwargs)
        self.scheduler.enterabs(runtime, 1000 + job.priority, self._run, argument=(job,))

    def start(self: CronScheduler) -> None:
        logger.debug("Starting scheduler")
        self.started = True
        for job in self.jobs:
            logger.debug(f"Starting job {job.name}")
            self._run(job)
        self.scheduler.run()

    def cancel(self: CronScheduler) -> None:
        self.started = False
        # Cancel all futur events
        for event in self.scheduler.queue:
            logger.debug(f"Canceling {event}")
            self.scheduler.cancel(event)


class Job():

    def __init__(self: Job, name: str, expression: str, priority: int,
                 call: Callable[..., None], args: Dict[str, Any], inject_run_date: bool):
        self.name = name
        self.expression = expression
        self.priority = priority
        self.call = call
        self.args = args
        self.inject_run_date = inject_run_date
        self.cron = croniter(expression, timezone.localize(datetime.now()))
