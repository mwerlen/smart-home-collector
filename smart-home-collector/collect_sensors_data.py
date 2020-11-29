#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
# Inspired from : https://github.com/jcarduino/rtl_433_2db

import subprocess
import sched
import time
from datetime import datetime, timedelta
import threading
import queue
import json
import signal
import sys
import psycopg2
import psycopg2.errorcodes
import traceback

db_config = {
  'user': 'metrics',
  'password': 'metrics',
  'host': 'localhost',
  'database': 'metrics'
}
config = {
  'wait_seconds': 10,
  'schema': 'public',
  'debug': True
}

scheduler = sched.scheduler(time.time, time.sleep)
process = None
stdout_queue = queue.Queue()
stdout_reader = None

add_sensordata = ("INSERT INTO " + config['schema'] + ".sensor_data "
                  "(sensor_id, whatdata, data) "
                  "VALUES (%s, %s, %s)")


class AsynchronousFileReader(threading.Thread):
    '''
    Helper class to implement asynchronous reading of a file
    in a separate thread. Pushes read lines on a queue to
    be consumed in another thread.
    '''

    def __init__(self, fd, myqueue):
        assert isinstance(myqueue, queue.Queue)
        assert callable(fd.readline)
        threading.Thread.__init__(self)
        self._fd = fd
        self._queue = myqueue

    def run(self):
        '''The body of the tread: read lines and put them on the queue.'''
        for line in iter(self._fd.readline, ''):
            self._queue.put(line)

    def eof(self):
        '''Check whether there is no more content to expect.'''
        return not self.is_alive() and self._queue.empty()


def start_subprocess(args):
    '''
    Example of how to consume standard output and standard error of
    a subprocess asynchronously without risk on deadlocking.
    '''
    print("\nStarting sub process " + ' '.join(args) + "\n")

    # Launch the command as subprocess.
    global process
    process = subprocess.Popen(args,
                               bufsize=1,
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               text=True)

    # Launch the asynchronous readers of the process' stdout and stderr.
    global stdout_queue
    global stdout_reader
    stdout_reader = AsynchronousFileReader(process.stdout, stdout_queue)
    stdout_reader.start()


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
    TABLES['SensorData'] = (
        "CREATE TABLE IF NOT EXISTS " + config['schema'] + ".sensors_data ("
        "  \"sensor_id\" smallint not null,"
        "  \"type\" text NOT NULL,"
        "  \"data\" real NOT NULL,"
        "  \"timestamp\" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP"
        ")")
    for name, ddl in TABLES.items():
        try:
            print("Checking table {}: ".format(name))
            cursor.execute(ddl)
            connection.commit()
            cursor.close()
            connection.close()
        except psycopg2.DatabaseError as error:
            print_psycopg2_exception(error)


def sanitize(text):
    return text.replace(" ", "_")


def next_run():
    now = datetime.now()
    base = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
    next_run = base + timedelta(seconds=config['wait_seconds'])
    return next_run


def process_inputs():
    rundate = next_run()
    runtime = rundate.timestamp()
    if config['debug']:
        print("-------------")
        print(f"Next run at {str(rundate)}")
    scheduler.enterabs(runtime, 1, check_reader)
    scheduler.enterabs(runtime, 2, read_data)
    scheduler.enterabs(runtime, 3, check_process)
    scheduler.enterabs(runtime, 4, process_inputs)


def check_reader():
    if stdout_reader.eof():
        print("Stdout is EOF !")
        close_all()


def read_data():
    while not stdout_queue.empty():
        line = stdout_queue.get()

        if not line.startswith("{"):
            # this is a message from RTL_433, print it
            print(line.rstrip())
        else:
            # This is Json data, load it
            if config['debug']:
                print(line.rstrip())

            # {
            #   "time" : "2020-11-20 20:06:45",
            #   "brand" : "LaCrosse",
            #   "model" : "LaCrosse-TX29IT",
            #   "id" : 7,
            #   "battery_ok" : 1,
            #   "newbattery" : 0,
            #   "temperature_C" : 4.000,
            #   "mic" : "CRC"
            # }
            data = json.loads(line)
            label = sanitize(data["model"])

            if "channel" in data:
                label += ".CH=" + str(data["channel"])
            elif "id" in data:
                label += ".ID=" + str(data["id"])

            if "battery_ok" in data:
                if data["battery_ok"] == 0:
                    print(f'⚠ {label} Battery empty!')

            if "temperature_C" in data:
                print(f'Received from {label} : Temperature {data["temperature_C"]}')

            if "humidity" in data:
                print(label + ' Humidity ', data["humidity"])


def save_metrics():
    try:
        # Open connection
        print("Connecting to database...")
        connection = psycopg2.connect(db_config)
        cursor = connection.cursor()

        sensordata = ("tota", "toto", "titi")
        cursor.execute(add_sensordata, sensordata)

        # Make sure data is committed to the database
        connection.commit()
        cursor.close()
        connection.close()
        print("Done !")
    except psycopg2.DatabaseError as error:
        print_psycopg2_exception(error)
        print("Error connecting to database")


def check_process():
    if process.poll() is not None:
        print(f'Return code from RTL_433 : {process.poll()}')
        close_all()


def close_all():
    print("Closing down")

    # Cancel all futur events
    for event in scheduler.queue:
        print(f"Canceling {event}")
        scheduler.cancel(event)

    # try:
    #     cursor.close()
    #     cnx.close()
    # except:
    #     pass

    # Close subprocess' file descriptors.
    if stdout_reader is not None:
        stdout_reader.join()
    if process is not None:
        process.stdout.close()

    # Terminate subprocess
    if process is not None and process.poll() is None:
        process.terminate()

    exit()


def signal_handler(sig, frame):
    print("SIGINT signal received")
    close_all()
    sys.exit(0)


if __name__ == '__main__':
    # connect_db()
    check_database()
    start_subprocess(["/usr/local/bin/rtl_433",
                      "-C", "si",
                      "-f", "868M",
                      "-F", "json",
                      "-M", "utc",
                      "-R76"])
    signal.signal(signal.SIGINT, signal_handler)
    time.sleep(1)
    read_data()
    process_inputs()
    scheduler.run()
    close_all()
