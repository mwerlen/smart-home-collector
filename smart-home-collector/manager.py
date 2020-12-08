from __future__ import annotations
from typing import Dict, List, Any
from sensors.tx29it import TX29IT
from queue import Queue
from sensors.sensor import Sensor
from sensors.measure import Measure
from datetime import datetime
import logging

logger = logging.getLogger('manager')


class Manager():

    def __init__(self, message_queue: Queue[Dict[str, Any]], measure_queue: Queue[Measure]):
        self.tx29it = TX29IT()
        self.sensors: List[Sensor] = [self.tx29it]
        self.message_queue: Queue[Dict[str, Any]] = message_queue
        self.measure_queue: Queue[Measure] = measure_queue

    def dispatch_messages(self: Manager) -> None:
        while not self.message_queue.empty():
            message: Dict[str, Any] = self.message_queue.get()
            if 'idsensor' not in message:
                logger.error(f"Message without idsensor : {message}")
            elif message['idsensor'] == TX29IT.IDSENSOR:
                self.tx29it.process_incoming_message(message)
            else:
                logger.warn(f"Unknown message from {message['idsensor']}")

    def publish_measures(self: Manager, timestamp: datetime) -> None:
        for sensor in self.sensors:
            measures = sensor.get_measures(timestamp)
            for measure in measures:
                logger.info(f"{measure}")
                self.measure_queue.put(measure)

    def messages_to_measures(self: Manager, rundate: datetime) -> None:
        self.dispatch_messages()
        self.publish_measures(rundate)
