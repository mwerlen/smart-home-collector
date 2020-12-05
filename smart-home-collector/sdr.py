import subprocess
import json
import threading
from datetime import datetime
from typing import Dict
from queue import Queue


def sanitize(text):
    return text.replace(" ", "_")


class SignalReader(threading.Thread):

    def __init__(self, config: Dict, message_queue: Queue):
        threading.Thread.__init__(self)
        self.config = config
        self.message_queue = message_queue

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

                message = json.loads(line)
                label = sanitize(message["model"])
                acquisitiondate = datetime.now()

                if "channel" in message:
                    label += ".CH=" + str(message["channel"])
                elif "id" in message:
                    label += ".ID=" + str(message["id"])

                message['idsensor'] = label
                message['acquisitiondate'] = acquisitiondate

                self.message_queue.put(message)

            if not self.is_alive():
                self.close()

        if self.process.poll() is not None:
            print(f'Return code from RTL_433 [{self.process.pid}]: {self.process.poll()}')
            self.close()

    def close(self):
        # Terminate subprocess
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
