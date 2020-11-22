#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
import subprocess
import time
import threading
import queue
import json
import signal
import sys

# import mysql.connector
# from mysql.connector import errorcode

# Forked from : https://github.com/jcarduino/rtl_433_2db

# Please create a mysql database for user rtl433db with create rights so table
# can be created
# change ip for database server
# install mysql connector
# install phython 2.7
# let it run ;)

bdd_config = {
  'user': 'rtl433db',
  'password': 'fWMqwmFNKbK9upjT',
  'host': '192.168.0.8',
  'database': 'rtl433db',
  'raise_on_warnings': True
}
config = {
  'wait_time': 1,
  'debug': False
}

process = None
stdout_queue = queue.Queue()
stdout_reader = None


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


# def connect_db():
#    # do database stuff init
#    try:
#        print("Connecting to database")
#        cnx = mysql.connector.connect(**config)
#    except mysql.connector.Error as err:
#        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
#            print("Something is wrong with your user name or password")
#        elif err.errno == errorcode.ER_BAD_DB_ERROR:
#            print("Database does not exists")
#            print("please create it before using this script")
#            print("Tables can be created by the script.")
#        else:
#            print(err)
#    reconnectdb=0#if 0 then no error or need ro be reconnected
#    #else:
#    #cnx.close()
#    cursor = cnx.cursor()
#    TABLES = {}
#    TABLES['SensorData'] = (
#        "CREATE TABLE `SensorData` ("
#        "  `sensor_id` INT UNSIGNED NOT NULL,"
#        "  `whatdata` varchar(50) NOT NULL,"
#        "  `data` float NOT NULL,"
#        "  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
#        ") ENGINE =InnoDB DEFAULT CHARSET=latin1")
#    for name, ddl in TABLES.iteritems():
#        try:
#            print("Checking table {}: ".format(name))
#            cursor.execute(ddl)
#        except mysql.connector.Error as err:
#            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
#                print("Table seams to exist, no need to create it.")
#            else:
#                print(err.msg)
#        else:
#            print("OK")
#    add_sensordata= ("INSERT INTO SensorData "
#                     "(sensor_id, whatdata, data) "
#                     "VALUES (%s, %s, %s)")


def sanitize(text):
    return text.replace(" ", "_")


def process_inputs():
    # do queue loop, entering data to database
    # Check the queues if we received some output
    # (until there is nothing more to get).
    while True:

        if stdout_reader.eof():
            print("Stdout is EOF !")
            return False

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
                when = int(time.time())
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

                #######################
                # last field, put in db
                # UPDATE DB
                #########################
                # try:
                #     if reconnectdb:
                #         print("Trying reconnecting to database")
                #      #   cnx.reconnect()
                #         reconnectdb=0
                #     print("Kaku ID "+str(device)+" Unit "+unit+" Grp"+group+" Do "+command+" Dim "+dim)
                #     sensordata = (device,'Kaku '+unit+' Grp'+group+" Do "+command+ ' Dim '+ dim,dimvalue)
                #     #cursor.execute(add_sensordata,sensordata)
                #     # Make sure data is committed to the database
                #     print("committing")
                #     #cnx.commit()
                # except mysql.connector.Error as err:
                #     if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                #         print("Table seams to exist, no need to create it.")
                #     else:
                #         print(err.msg)
                #     reconnectdb=1
                #     print("Error connecting to database")

        if process.poll() is not None:
            print(f'Return code from RTL_433 : {process.poll()}')
            return False

        # Sleep a bit before asking the readers again.
        time.sleep(config['wait_time'])


def close_all():
    print("Closing down")
    # try:
    #     cursor.close()
    #     cnx.close()
    # except:
    #     pass

    # Close subprocess' file descriptors.
    stdout_reader.join()
    process.stdout.close()

    # Terminate subprocess
    if process.poll() is None:
        process.terminate()


def signal_handler(sig, frame):
    print("SIGINT signal received")
    close_all()
    sys.exit(0)


if __name__ == '__main__':
    # connect_db()
    start_subprocess(["/usr/local/bin/rtl_433",
                      "-C", "si",
                      "-f", "868M",
                      "-F", "json",
                      "-M", "utc",
                      "-R76"])
    signal.signal(signal.SIGINT, signal_handler)
    process_inputs()
    close_all()
