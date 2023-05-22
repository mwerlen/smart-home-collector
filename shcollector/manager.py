from __future__ import annotations
from typing import Dict, Any
from sensors.lacrossetx29it import LaCrosseTX29IT
from sensors.thermoprotx2c import ThermoProTX2C
from queue import Queue
from sensors.sensor import Sensor
from sensors.measure import Measure
from datetime import datetime
import logging
import cfg


logger = logging.getLogger('manager')


class Manager:

    def __init__(self, message_queue: Queue[Dict[str, Any]], measure_queue: Queue[Measure]):
        self.sensors: Dict[str, Sensor] = {}
        self.build_sensors()
        self.message_queue: Queue[Dict[str, Any]] = message_queue
        self.measure_queue: Queue[Measure] = measure_queue
        self.latest_values: Dict[int, Measure] = {}

    def build_sensors(self: Manager) -> None:
        for section_name in cfg.config.sections():
            if section_name.startswith("sensor:"):
                section = cfg.config[section_name]
                sensor_type = section['type']
                if sensor_type == LaCrosseTX29IT.SENSOR_TYPE_NAME:
                    sensor = LaCrosseTX29IT(
                        section['radio_id'],
                        section['database_id'],
                        section['name'],
                        section['location'])
                    self.sensors[section['radio_id']] = sensor
                    logger.debug(f"Registered sensor : {section['name']}")
                elif sensor_type == ThermoProTX2C.SENSOR_TYPE_NAME:
                    sensor = ThermoProTX2C(
                        section['radio_id'],
                        section['database_id'],
                        section['name'],
                        section['location'])
                    self.sensors[section['radio_id']] = sensor
                    logger.debug(f"Registered sensor : {section['name']}")
                else:
                    logger.warning(f"Unknown sensor config {section_name} with type {sensor_type}")
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
                logger.warning(f"Unknown message from {message['radio_id']}")

    def publish_measures(self: Manager, timestamp: datetime) -> None:
        for sensor in self.sensors.values():
            measures = sensor.get_measures(timestamp)
            for measure in measures:
                latest_val = self.latest_values.get(measure.get_cache_key())
                if latest_val and abs(latest_val.data - measure.data) > measure.metric.threshold():
                    logger.info(f"Incoherent value (Δ > {measure.metric.threshold()}) : {measure}")
                else:
                    logger.info(f"{measure}")
                    self.measure_queue.put(measure)
                    self.latest_values[measure.get_cache_key()] = measure

    def messages_to_measures(self: Manager, run_date: datetime) -> None:
        self.dispatch_messages()
        self.publish_measures(run_date)
