#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
# Inspired from : https://github.com/jcarduino/rtl_433_2db

import subprocess
import sched
import time
from datetime import datetime
import threading
import queue
import json
import signal
import sys
import psycopg2
import psycopg2.errorcodes
import traceback
from croniter import croniter
import pytz


timezone = pytz.timezone('Europe/Paris')

db_config = {
  'user': 'metrics',
  'password': 'metrics',
  'host': 'localhost',
  'database': 'metrics'
}

config = {
  'read_data_cron': '* * * * * 0,10,20,30,40,50',   # every 10 secondes
  'write_data_cron': '*/10 * * * *',  # every 10 minutes
  'schema': 'public',
  'debug': True
}

scheduler = sched.scheduler(time.time, time.sleep)
read_cron = croniter(config['read_data_cron'], timezone.localize(datetime.now()))
write_cron = croniter(config['write_data_cron'], timezone.localize(datetime.now()))
process = None
stdout_queue = queue.Queue()
stdout_reader = None

add_sensordata = ("INSERT INTO " + config['schema'] + ".sensors_data "
                  "(idsensor, data, time) "
                  "VALUES ('{0}', {1}, '{2}')")

measures = []


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
    TABLES['sensors'] = (
        "CREATE TABLE IF NOT EXISTS " + config['schema'] + ".sensors ("
        "  \"idsensor\" text PRIMARY KEY,"
        "  \"name\" text NOT NULL,"
        "  \"metric\" text not null,"
        "  \"location\" text"
        ");")
    TABLES['sensors_data'] = (
        "CREATE TABLE IF NOT EXISTS " + config['schema'] + ".sensors_data ("
        "  \"idsensor\" text REFERENCES " + config['schema'] + ".sensors,"
        "  \"data\" real NOT NULL,"
        "  \"time\" timestamp  with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,"
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


def sanitize(text):
    return text.replace(" ", "_")


def process_inputs():
    rundate = read_cron.get_next(datetime)
    while rundate <= timezone.localize(datetime.now()):
        rundate = read_cron.get_next(datetime)
    runtime = rundate.timestamp()
    if config['debug']:
        print("-------------")
        print(f"Next read run at {str(rundate)}")
    scheduler.enterabs(runtime, 1, check_reader)
    scheduler.enterabs(runtime, 2, read_measures, argument=(rundate,))
    scheduler.enterabs(runtime, 3, write_measures)
    scheduler.enterabs(runtime, 4, check_process)
    scheduler.enterabs(runtime, 5, process_inputs)


def check_reader():
    if stdout_reader.eof():
        print("Stdout is EOF !")
        close_all()


def read_measures(rundate=datetime.now()):
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
            measure = json.loads(line)
            label = sanitize(measure["model"])

            if "channel" in measure:
                label += ".CH=" + str(measure["channel"])
            elif "id" in measure:
                label += ".ID=" + str(measure["id"])

            if "battery_ok" in measure:
                if measure["battery_ok"] == 0:
                    print(f'⚠ {label} Battery empty!')

            if "temperature_C" in measure:
                print(f'Received from {label} : Temperature {measure["temperature_C"]}')

            if "humidity" in measure:
                print(label + ' Humidity ', measure["humidity"])

            measures.append((label, measure["temperature_C"], rundate))


def write_measures():
    try:
        # Open connection
        print("Connecting to database...")
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        for measure in measures:
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
    read_measures()
    process_inputs()
    scheduler.run()
    close_all()
