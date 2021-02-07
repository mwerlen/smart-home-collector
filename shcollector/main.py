#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
# Inspired from : https://github.com/jcarduino/rtl_433_2db

import logging
import sys
import argparse
import signal
from queue import Queue
from typing import Any, Dict, NoReturn, List, Callable, Optional

from reporters.database import Database
from sensors.measure import Measure
from manager import Manager
from utils.cron import CronScheduler, Job
from sdr import SignalReader
import cfg


logger = logging.getLogger('main')
kill_callback: List[Callable[[], None]] = []
close_callback: List[Callable[[], None]] = []


def close_all() -> NoReturn:
    logger.info("Closing down")

    # On appelle tous les callback de d'arrêt
    for callback in kill_callback:
        callback()

    # bye
    sys.exit(0)


def interrup_signal_handler(sig: int, frame: Any) -> NoReturn:
    logger.warning("SIGINT signal received")
    close_all()
    sys.exit(0)


def termination_signal_handler(sig: int, frame: Any) -> NoReturn:
    logger.warning("SIGTERM signal received")

    # On appelle tous les callback de fermture
    for callback in close_callback:
        callback()

    close_all()
    sys.exit(0)


def run(debug: bool, config_file: Optional[str]) -> None:
    # Handle signals
    signal.signal(signal.SIGINT, interrup_signal_handler)
    signal.signal(signal.SIGTERM, termination_signal_handler)

    # Apply config
    if config_file is not None:
        cfg.config.set_config_file(config_file)
    cfg.config.set_debug(debug)

    # Create queues
    message_queue: Queue[Dict[str, Any]] = Queue()
    measure_queue: Queue[Measure] = Queue()

    # Initialize CronScheduler
    cron: CronScheduler = CronScheduler()
    kill_callback.append(cron.cancel)

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

    kill_callback.append(close_reader)

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

    close_callback.append(database.write_measures)

    # Launch processes
    reader.start()
    cron.start()


if __name__ == '__main__':
    # handle flags
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Activer les logs de debug", action="store_true")
    parser.add_argument("-c", "--config", help="Spécifier un fichier de configuration")
    args = parser.parse_args()

    run(args.debug, args.config)
