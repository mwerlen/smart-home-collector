from __future__ import annotations
from typing_extensions import Protocol
from typing import Dict, List, Type, Any
from sensors.metrics import Types
from sensors.measure import Measure
from datetime import datetime


class Sensor(Protocol):

    def get_sensor_definition(self: Sensor) -> SensorDefinition:
        pass

    @classmethod
    def get_sensor_metric_types(cls: Type[Sensor]) -> List[Types]:
        pass

    def process_incoming_message(self: Sensor, message: Dict[str, Any]) -> None:
        pass

    def get_measures(self: Sensor, timestamp: datetime) -> List[Measure]:
        pass


class SensorDefinition(object):

    def __init__(self: SensorDefinition, radio_id: str, database_id: str, name: str, location: str):
        self.radio_id = radio_id
        self.database_id = database_id
        self.name = name
        self.location = location
