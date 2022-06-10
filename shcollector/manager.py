from __future__ import annotations
from typing import Dict, Any
from sensors.tx29it import TX29IT
from queue import Queue
from sensors.sensor import Sensor
from sensors.measure import Measure
from datetime import datetime
import logging
import cfg

logger = logging.getLogger('manager')


class Manager():

    def __init__(self, message_queue: Queue[Dict[str, Any]], measure_queue: Queue[Measure]):
        self.sensors: Dict[str, Sensor] = {}
        self.build_sensors()
        self.message_queue: Queue[Dict[str, Any]] = message_queue
        self.measure_queue: Queue[Measure] = measure_queue

    def build_sensors(self: Manager) -> None:
        for section_name in cfg.config.sections():
            if section_name.startswith("sensor:"):
                section = cfg.config[section_name]
                sensor_type = section['type']
                if sensor_type == TX29IT.SENSOR_TYPE_NAME:
                    sensor = TX29IT(
                        section['radio_id'],
                        section['database_id'],
                        section['name'],
                        section['location'])
                    self.sensors[section['radio_id']] = sensor
                    logger.debug(f"Registered sensor : {section['name']}")
                else:
                    logger.warn(f"Unknown sensor config {section_name} with type {sensor_type}")
                    continue
            else:
                pass

    def dispatch_messages(self: Manager) -> None:
        while not self.message_queue.empty():
            message: Dict[str, Any] = self.message_queue.get()
            if 'radio_id' not in message:
                logger.error(f"Message without radio_id : {message}")
            elif message['radio_id'] in self.sensors.keys():
                sensor = self.sensors[message['radio_id']]
                sensor.process_incoming_message(message)
            else:
                logger.warn(f"Unknown message from {message['radio_id']}")

    def publish_measures(self: Manager, timestamp: datetime) -> None:
        for sensor in self.sensors.values():
            measures = sensor.get_measures(timestamp)
            for measure in measures:
                logger.info(f"{measure}")
                self.measure_queue.put(measure)

    def messages_to_measures(self: Manager, rundate: datetime) -> None:
        self.dispatch_messages()
        self.publish_measures(rundate)
