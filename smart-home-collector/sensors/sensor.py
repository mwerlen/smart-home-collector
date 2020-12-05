from __future__ import annotations
from typing_extensions import Protocol
from typing import Dict, List
from sensors.metrics import Types
from datetime import datetime


class Sensor(Protocol):

    @classmethod
    def get_sensor_definition(cls) -> Dict[str, str]:
        pass

    @classmethod
    def get_sensor_metric_types(cls) -> List[Types]:
        pass

    def process_incoming_message(self: Sensor, message: Dict):
        pass

    def get_measures(self: Sensor, timestamp: datetime) -> list:
        pass
