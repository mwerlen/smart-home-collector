from __future__ import annotations
from sensors.metrics import Types
from sensors.measure import Measure
from sensors.sensor import SensorDefinition
from typing import Dict, Optional, List, Type
from datetime import datetime


class TX29IT:

    IDSENSOR = 'LaCrosse-TX29IT.ID=7'

    SENSOR_DEFINITION: SensorDefinition = SensorDefinition(
        IDSENSOR,
        'Thermomètre extérieur',
        'Extérieur - Nord'
    )

    METRIC_TYPES = [Types.TEMPERATURE, Types.BATTERY]

    def __init__(self):
        self.latest_temperature: Optional[float] = None
        self.latest_battery_ok: Optional[bool] = None

    @classmethod
    def get_sensor_definition(cls: Type[TX29IT]) -> SensorDefinition:
        return TX29IT.SENSOR_DEFINITION

    @classmethod
    def get_sensor_metric_types(cls: Type[TX29IT]) -> List[Types]:
        return TX29IT.METRIC_TYPES

    def process_incoming_message(self: TX29IT, message: Dict):
        if "battery_ok" in message:
            self.latest_battery_ok = message['battery_ok']

        if "temperature_C" in message:
            print(f'Received from {TX29IT.IDSENSOR} : Temperature {message["temperature_C"]}')
            self.latest_temperature = message['temperature_C']

    def get_measures(self: TX29IT, time: datetime) -> List[Measure]:
        measures: List[Measure] = []
        if self.latest_temperature is not None:
            measures.append(Measure(time,
                            TX29IT.IDSENSOR,
                            Types.TEMPERATURE,
                            self.latest_temperature))

        if self.latest_battery_ok is not None:
            measures.append(Measure(time,
                            TX29IT.IDSENSOR,
                            Types.BATTERY,
                            self.latest_battery_ok))

        return measures
