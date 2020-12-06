#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
# Inspired from : https://github.com/jcarduino/rtl_433_2db

import logging
import sched
import time
import sys
from datetime import datetime
import signal
from croniter import croniter
import pytz
from queue import Queue
from reporters.database import Database
from sensors.manager import Manager
from sensors.measure import Measure
from typing import Any, Dict, NoReturn

from sdr import SignalReader
import cfg


logger = logging.getLogger('main')

reader: SignalReader

timezone = pytz.timezone('Europe/Paris')

config = {
  'write_data_cron': '* * * * * 0,30',  # every 2 minutes
  'process_data_cron': '* * * * * 0,15,30,45',   # every minute
}

scheduler = sched.scheduler(time.time, time.sleep)
process_cron = croniter(cfg.config.get('Cron', 'process_data_cron'), timezone.localize(datetime.now()))
write_cron = croniter(cfg.config.get('Cron', 'write_data_cron'), timezone.localize(datetime.now()))


def get_measures(manager: Manager) -> None:
    rundate = write_cron.get_next(datetime)
    while rundate <= timezone.localize(datetime.now()):
        rundate = write_cron.get_next(datetime)
    runtime = rundate.timestamp()
    logger.debug(f"Scheduling get_measures run at {str(rundate)}")
    scheduler.enterabs(runtime, 1, check_reader)
    scheduler.enterabs(runtime, 2, manager.dispatch_messages)
    scheduler.enterabs(runtime, 3, manager.publish_measures, argument=(rundate,))
    scheduler.enterabs(runtime, 3, get_measures, argument=(manager,))


def store_measures(database: Database) -> None:
    rundate = write_cron.get_next(datetime)
    while rundate <= timezone.localize(datetime.now()):
        rundate = write_cron.get_next(datetime)
    runtime = rundate.timestamp()
    logger.debug(f"Scheduling store_measures run at {str(rundate)}")
    scheduler.enterabs(runtime, 2, database.write_measures)
    scheduler.enterabs(runtime, 3, store_measures, argument=(database,))


def check_reader() -> None:
    if not reader.is_alive():
        close_all()


def close_all() -> NoReturn:
    logger.info("Closing down")

    # Cancel all futur events
    for event in scheduler.queue:
        logger.debug(f"Canceling {event}")
        scheduler.cancel(event)

    reader.close()
    reader.join()

    sys.exit(0)


def signal_handler(sig: int, frame: Any) -> NoReturn:
    logger.warning("SIGINT signal received")
    close_all()
    sys.exit(0)


def run() -> None:
    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)

    # Create queues
    message_queue: Queue[Dict[str, Any]] = Queue()
    measure_queue: Queue[Measure] = Queue()

    # Initialize database
    database: Database = Database(measure_queue)

    # Initialize sensor manager
    manager = Manager(message_queue, measure_queue)

    # Initialize SDR reader
    global reader
    reader = SignalReader(message_queue)

    # Update database structure
    database.check_structure()
    database.check_sensors_definition(manager)

    # Launch processes
    get_measures(manager)
    store_measures(database)
    reader.start()
    scheduler.run(blocking=True)

    # Close all
    close_all()


if __name__ == '__main__':
    run()
