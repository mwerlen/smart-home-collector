from __future__ import annotations
from typing import Dict, List, Any
from sensors.tx29it import TX29IT
from queue import Queue
from sensors.sensor import Sensor
from sensors.measure import Measure
from datetime import datetime


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
                print(f"Message without idsensor : {message}")
            elif message['idsensor'] == TX29IT.IDSENSOR:
                self.tx29it.process_incoming_message(message)
            else:
                print(f"Unknown message from {message['idsensor']}")

    def publish_measures(self: Manager, timestamp: datetime) -> None:
        for sensor in self.sensors:
            measures = sensor.get_measures(timestamp)
            for measure in measures:
                print(f"Got new measure : {measure}")
                self.measure_queue.put(measure)
