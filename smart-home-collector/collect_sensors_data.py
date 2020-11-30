#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
# Inspired from : https://github.com/jcarduino/rtl_433_2db

import sched
import time
from datetime import datetime
import signal
import sys
import psycopg2
import psycopg2.errorcodes
import traceback
from croniter import croniter
import pytz
import queue

from sdr import SignalReader

timezone = pytz.timezone('Europe/Paris')

reader = None

db_config = {
  'user': 'metrics',
  'password': 'metrics',
  'host': 'localhost',
  'database': 'metrics'
}

config = {
  'read_data_cron': '* * * * * 0,10,20,30,40,50',   # every 10 secondes
  'write_data_cron': '* * * * * 5,15,25,35,45,55',  # every 10 minutes
  'schema': 'public',
  'debug': True,
  'commandline': ["/usr/local/bin/rtl_433", "-C", "si", "-f", "868M", "-F", "json", "-M", "utc", "-R76"]
}

scheduler = sched.scheduler(time.time, time.sleep)
write_cron = croniter(config['write_data_cron'], timezone.localize(datetime.now()))

add_sensordata = ("INSERT INTO " + config['schema'] + ".sensors_data "
                  "(time, idsensor, data) "
                  "VALUES ('{0}', '{1}', {2})")

measures = queue.Queue()


def print_psycopg2_exception(error):
    # get details about the exception
    error_type, error_obj, stacktrace = sys.exc_info()

    # get the line number when exception occured
    line_num = stacktrace.tb_lineno

    # print the connect() error
    print(f"\n[{error.pgcode}] {error_type.__name__} on line number {line_num} :\n{error.pgerror} ")

    if config['debug']:
        # stacktrace
        traceback.print_tb(stacktrace)
        # print(f"\nextensions.Diagnostics: {str(error.diag)}")

    close_all()


def check_database():
    try:
        print("Connecting to database")
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
    except psycopg2.DatabaseError as error:
        print_psycopg2_exception(error)

    TABLES = {}
    TABLES['sensors'] = (
        "CREATE TABLE IF NOT EXISTS " + config['schema'] + ".sensors ("
        "  \"idsensor\" text PRIMARY KEY,"
        "  \"name\" text NOT NULL,"
        "  \"metric\" text not null,"
        "  \"location\" text"
        ");")
    TABLES['sensors_data'] = (
        "CREATE TABLE IF NOT EXISTS " + config['schema'] + ".sensors_data ("
        "  \"time\" timestamp  with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,"
        "  \"idsensor\" text REFERENCES " + config['schema'] + ".sensors,"
        "  \"data\" real NOT NULL,"
        "  PRIMARY KEY (time,idsensor)"
        ");")

    for name, ddl in TABLES.items():
        try:
            print(f"Checking table {name}")
            cursor.execute(ddl)
        except psycopg2.DatabaseError as error:
            print_psycopg2_exception(error)

    SENSORS = {}
    SENSORS['LaCrosse-TX29IT.ID=7'] = (
        "INSERT INTO " + config['schema'] + ".sensors"
        "  VALUES ('LaCrosse-TX29IT.ID=7',"
        "          'Thermomètre extérieur',"
        "          'Température',"
        "          'Extérieur - Nord')"
        "  ON CONFLICT (idsensor) DO "
        "       UPDATE SET name=excluded.name,"
        "                  metric=excluded.metric,"
        "                  location=excluded.location"
        ";")

    for name, ddl in SENSORS.items():
        try:
            print(f"Checking sensor {name}")
            cursor.execute(ddl)
        except psycopg2.DatabaseError as error:
            print_psycopg2_exception(error)

    connection.commit()
    cursor.close()
    connection.close()


def store_measures():
    rundate = write_cron.get_next(datetime)
    while rundate <= timezone.localize(datetime.now()):
        rundate = write_cron.get_next(datetime)
    runtime = rundate.timestamp()
    if config['debug']:
        print(f"Scheduling next write run at {str(rundate)}")
    scheduler.enterabs(runtime, 1, write_measures)
    scheduler.enterabs(runtime, 1, store_measures)


def write_measures():
    try:
        # Open connection
        print("Connecting to database...")
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        while not measures.empty():
            measure = measures.get()
            print(measure)
            dml = add_sensordata.format(*measure)
            if config['debug']:
                print(f"DML : {dml}")
            cursor.execute(dml)

        # Make sure data is committed to the database
        connection.commit()
        cursor.close()
        connection.close()
        print("Done !")
    except psycopg2.DatabaseError as error:
        print_psycopg2_exception(error)
        print("Error connecting to database")


def close_all():
    print("Closing down")

    # Cancel all futur events
    for event in scheduler.queue:
        print(f"Canceling {event}")
        scheduler.cancel(event)

    reader.close()
    reader.join()

    sys.exit(0)


def signal_handler(sig, frame):
    print("SIGINT signal received")
    close_all()
    sys.exit(0)


if __name__ == '__main__':
    # Handle signals
    signal.signal(signal.SIGINT, signal_handler)

    # connect_db()
    check_database()
    reader = SignalReader(config, measures)
    reader.start()
    store_measures()
    scheduler.run(blocking=True)
    close_all()
