#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
# Inspired from : https://github.com/jcarduino/rtl_433_2db

import logging
import sys
import signal
from queue import Queue
from typing import Any, Dict, NoReturn, List, Callable

from reporters.database import Database
from sensors.measure import Measure
from manager import Manager
from utils.cron import CronScheduler, Job
from sdr import SignalReader
import cfg


logger = logging.getLogger('main')
closebacks: List[Callable[[], None]] = []


def close_all() -> NoReturn:
    logger.info("Closing down")

    # On appelle tous les callback de fermeture
    for closeback in closebacks:
        closeback()

    # bye
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

    # Initialize CronScheduler
    cron: CronScheduler = CronScheduler()
    closebacks.append(cron.cancel)

    # Initialize database
    database: Database = Database(measure_queue)

    # Initialize sensor manager
    manager = Manager(message_queue, measure_queue)

    # Initialize SDR reader
    reader = SignalReader(message_queue)

    # Close function
    def close_reader() -> None:
        reader.close()
        reader.join()

    closebacks.append(close_reader)

    # check function
    def check_reader() -> None:
        if not reader.is_alive():
            close_all()

    # Update database structure
    database.check_structure()
    database.check_sensors_definition(manager)

    # Schedule jobs
    check_reader_job: Job = Job('check_reader',
                                cfg.config.get('Cron', 'process_data_cron'),
                                1,
                                check_reader,
                                {},
                                False)
    cron.schedule(check_reader_job)

    process_messages_job: Job = Job('process_messages',
                                    cfg.config.get('Cron', 'process_data_cron'),
                                    2,
                                    manager.messages_to_measures,
                                    {},
                                    True)
    cron.schedule(process_messages_job)

    store_measures_job: Job = Job('store_measures',
                                  cfg.config.get('Cron', 'write_data_cron'),
                                  3,
                                  database.write_measures,
                                  {},
                                  False)
    cron.schedule(store_measures_job)

    # Launch processes
    reader.start()
    cron.start()


if __name__ == '__main__':
    run()
