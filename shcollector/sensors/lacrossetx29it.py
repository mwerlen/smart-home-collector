from __future__ import annotations
from sensors.metrics import Types
from sensors.measure import Measure
from sensors.sensor import SensorDefinition
from typing import Dict, Optional, List, Type, Any
from datetime import datetime
import logging

logger = logging.getLogger("LaCrosse-tx29it")


class LaCrosseTX29IT:

    SENSOR_TYPE_NAME = "LaCrosse-TX29IT"
    METRIC_TYPES = [Types.TEMPERATURE, Types.BATTERY]

    def __init__(self: LaCrosseTX29IT, radio_id: str, database_id: str, name: str, location: str):
        self.latest_temperature: Optional[float] = None
        self.latest_battery_ok: Optional[bool] = None
        self.radio_id: str = radio_id
        self.database_id: str = database_id
        self.sensor_definition: SensorDefinition = SensorDefinition(radio_id,
                                                                    database_id,
                                                                    name,
                                                                    location)

    def get_sensor_definition(self: LaCrosseTX29IT) -> SensorDefinition:
        return self.sensor_definition

    @classmethod
    def get_sensor_metric_types(cls: Type[LaCrosseTX29IT]) -> List[Types]:
        return LaCrosseTX29IT.METRIC_TYPES

    def process_incoming_message(self: LaCrosseTX29IT, message: Dict[str, Any]) -> None:
        if "battery_ok" in message:
            self.latest_battery_ok = message['battery_ok']

        if "temperature_C" in message:
            logger.debug(f"Received from {self.radio_id} for {self.database_id} :"
                         f"Temperature {message['temperature_C']}")
            self.latest_temperature = message['temperature_C']

    def get_measures(self: LaCrosseTX29IT, time: datetime) -> List[Measure]:
        measures: List[Measure] = []
        if self.latest_temperature is not None:
            measures.append(Measure(time,
                            self.database_id,
                            Types.TEMPERATURE,
                            self.latest_temperature,
                            self.sensor_definition.location))
            self.latest_temperature = None

        if self.latest_battery_ok is not None:
            measures.append(Measure(time,
                            self.database_id,
                            Types.BATTERY,
                            self.latest_battery_ok,
                            self.sensor_definition.location))
            self.latest_battery_ok = None

        return measures
