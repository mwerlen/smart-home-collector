import subprocess
import json
import queue
import time
from datetime import datetime
from croniter import croniter
import pytz
import sched
import threading

from asyncreader import AsynchronousFileReader

timezone = pytz.timezone('Europe/Paris')


def sanitize(text):
    return text.replace(" ", "_")


class SignalReader(threading.Thread):

    def __init__(self, config, measures):
        threading.Thread.__init__(self)
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.read_cron = croniter(config['read_data_cron'], timezone.localize(datetime.now()))
        self.stdout_queue = queue.Queue()
        self.stdout_reader = None
        self.config = config
        self.measures = measures

    def run(self):
        self._start_subprocess()
        time.sleep(1)
        self.read_measures()  # First read to purge messages from RTL_433
        self.acquire_measures()
        self.scheduler.run(blocking=True)
        self.close()

    def _start_subprocess(self):
        '''
        Example of how to consume standard output and standard error of
        a subprocess asynchronously without risk on deadlocking.
        '''
        print("\nStarting sub process " + ' '.join(self.config['commandline']) + "\n")

        # Launch the command as subprocess.
        self.process = subprocess.Popen(self.config['commandline'],
                                        bufsize=1,
                                        shell=False,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True)

        # Launch the asynchronous readers of the process' stdout and stderr.
        self.stdout_reader = AsynchronousFileReader(self.process.stdout, self.stdout_queue)
        self.stdout_reader.start()

    def acquire_measures(self):
        rundate = self.read_cron.get_next(datetime)
        while rundate <= timezone.localize(datetime.now()):
            rundate = self.read_cron.get_next(datetime)
        runtime = rundate.timestamp()
        if self.config['debug']:
            print(f"Scheduling next read run at {str(rundate)}")
        self.scheduler.enterabs(runtime, 1, self.check_reader)
        self.scheduler.enterabs(runtime, 2, self.read_measures, argument=(rundate,))
        self.scheduler.enterabs(runtime, 4, self.check_process)
        self.scheduler.enterabs(runtime, 5, self.acquire_measures)

    def check_reader(self):
        if self.stdout_reader.eof():
            print("Stdout is EOF !")
            self.close()

    def read_measures(self, rundate=datetime.now()):
        while not self.stdout_queue.empty():
            line = self.stdout_queue.get()

            if not line.startswith("{"):
                # this is a message from RTL_433, print it
                print(line.rstrip())
            else:
                # This is Json data, load it
                if self.config['debug']:
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

                self.measures.put((rundate, label, measure["temperature_C"]))

    def check_process(self):
        if self.process.poll() is not None:
            print(f'Return code from RTL_433 : {self.process.poll()}')
            self.close()

    def close(self):
        # Cancel all futur events
        for event in self.scheduler.queue:
            print(f"Canceling {event}")
            self.scheduler.cancel(event)

        # Terminate subprocess
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()

        # Close subprocess' file descriptors.
        if self.stdout_reader is not None:
            self.stdout_reader.close()
        if self.process is not None:
            self.process.stdout.close()
