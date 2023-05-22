from __future__ import annotations
import subprocess
import json
import threading
import logging
from datetime import datetime
from typing import Dict, Any, List
from queue import Queue
import cfg

logger = logging.getLogger('sdr')


class SignalReader(threading.Thread):

    def __init__(self: SignalReader, message_queue: Queue[Dict[str, Any]]):
        threading.Thread.__init__(self)
        self.message_queue: Queue[Dict[str, Any]] = message_queue

    def get_command_line(self: SignalReader) -> List[str]:
        arguments = [cfg.config.get('RTL433', 'executable')]
        arguments.extend(["-C", cfg.config.get('RTL433', 'units')])
        arguments.extend(["-f", cfg.config.get('RTL433', 'frequency')])
        arguments.extend(["-F", "json"])
        arguments.extend(["-M", cfg.config.get('RTL433', 'timezone')])
        for device in cfg.config.get('RTL433', 'devices').split(','):
            arguments.extend(["-R", device.strip()])
        return arguments

    def run(self: SignalReader) -> None:
        logger.info("Starting sub process " + ' '.join(self.get_command_line()))

        # Launch the command as subprocess.
        self.process = subprocess.Popen(self.get_command_line(),
                                        bufsize=1,
                                        shell=False,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT,
                                        text=True)

        if self.process.stdout is None:
            self.close()
            return

        for line in iter(self.process.stdout.readline, ''):

            if not line.startswith("{"):
                # this is a message from RTL_433, log it
                logger.info(line.rstrip())
            else:
                # This is Json data, load it
                logger.debug(line.rstrip())

                message: Dict[str, Any] = json.loads(line)
                label: str = SignalReader.sanitize(message["model"])
                acquisition_date: datetime = datetime.now()

                if "channel" in message:
                    label += ".CH=" + str(message["channel"])
                elif "id" in message:
                    label += ".ID=" + str(message["id"])

                message['radio_id'] = label
                message['acquisition_date'] = acquisition_date

                self.message_queue.put(message)

            if not self.is_alive():
                self.close()

        if self.process.poll() is not None:
            logger.error(f'Return code from RTL_433 [{self.process.pid}]: {self.process.poll()}')
            self.close()

    @staticmethod
    def sanitize(text: str) -> str:
        return text.replace(" ", "_")

    def close(self: SignalReader) -> None:
        # Terminate subprocess
        if hasattr(self, 'process') and self.process is not None and self.process.poll() is None:
            self.process.terminate()
