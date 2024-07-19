from __future__ import annotations
from sensors.metrics import Types
from sensors.measure import Measure
from sensors.sensor import SensorDefinition
from typing import Dict, Optional, List, Type, Any
from datetime import datetime
import logging

logger = logging.getLogger("LaCrosse-tx35")


class LaCrosseTX35:

    SENSOR_TYPE_NAME = "LaCrosse-TX35"
    METRIC_TYPES = [Types.TEMPERATURE, Types.BATTERY, Types.HUMIDITY]

    def __init__(self: LaCrosseTX35, radio_id: str, database_id: str, name: str, location: str):
        self.latest_temperature: Optional[float] = None
        self.latest_humidity: Optional[int] = None
        self.latest_battery_ok: Optional[bool] = None
        self.radio_id: str = radio_id
        self.database_id: str = database_id
        self.sensor_definition: SensorDefinition = SensorDefinition(radio_id,
                                                                    database_id,
                                                                    name,
                                                                    location)

    def get_sensor_definition(self: LaCrosseTX35) -> SensorDefinition:
        return self.sensor_definition

    @classmethod
    def get_sensor_metric_types(cls: Type[LaCrosseTX35]) -> List[Types]:
        return LaCrosseTX35.METRIC_TYPES

    def process_incoming_message(self: LaCrosseTX35, message: Dict[str, Any]) -> None:
        if "battery_ok" in message:
            self.latest_battery_ok = message['battery_ok']

        if "humidity" in message:
            logger.debug(f"Received from {self.radio_id} for {self.database_id} :"
                         f"Humidity {message['humidity']}")
            self.latest_humidity = message['humidity']

        if "temperature_C" in message:
            logger.debug(f"Received from {self.radio_id} for {self.database_id} :"
                         f"Temperature {message['temperature_C']}")
            self.latest_temperature = message['temperature_C']

    def get_measures(self: LaCrosseTX35, time: datetime) -> List[Measure]:
        measures: List[Measure] = []
        if self.latest_temperature is not None:
            measures.append(Measure(time,
                            self.database_id,
                            Types.TEMPERATURE,
                            self.latest_temperature))
            self.latest_temperature = None

        if self.latest_humidity is not None:
            measures.append(Measure(time,
                            self.database_id,
                            Types.HUMIDITY,
                            self.latest_humidity))
            self.latest_humidity = None

        if self.latest_battery_ok is not None:
            measures.append(Measure(time,
                            self.database_id,
                            Types.BATTERY,
                            self.latest_battery_ok))
            self.latest_battery_ok = None

        return measures
