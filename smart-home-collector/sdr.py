import subprocess
import json
import threading
from datetime import datetime


def sanitize(text):
    return text.replace(" ", "_")


class SignalReader(threading.Thread):

    def __init__(self, config, measures):
        threading.Thread.__init__(self)
        self.config = config
        self.measures = measures

    def run(self):
        print("\nStarting sub process " + ' '.join(self.config['commandline']) + "\n")

        # Launch the command as subprocess.
        self.process = subprocess.Popen(self.config['commandline'],
                                        bufsize=1,
                                        shell=False,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True)

        for line in iter(self.process.stdout.readline, ''):

            if not line.startswith("{"):
                # this is a message from RTL_433, print it
                print(line.rstrip())
            else:
                # This is Json data, load it
                if self.config['debug']:
                    print(line.rstrip())

                measure = json.loads(line)
                label = sanitize(measure["model"])
                acquisitiondate = datetime.now()

                if "channel" in measure:
                    label += ".CH=" + str(measure["channel"])
                elif "id" in measure:
                    label += ".ID=" + str(measure["id"])

                if "battery_ok" in measure:
                    if measure["battery_ok"] == 0:
                        print(f'⚠ {label} Battery empty!')

                if "temperature_C" in measure:
                    print(f'Received from {label} : Temperature {measure["temperature_C"]}')

                # TODO put full object in queue
                self.measures.put((acquisitiondate, label, measure["temperature_C"]))

            if not self.is_alive():
                self.close()

        if self.process.poll() is not None:
            print(f'Return code from RTL_433 [{self.process.pid}]: {self.process.poll()}')
            self.close()

    def close(self):
        # Terminate subprocess
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
