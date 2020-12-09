from __future__ import annotations
from sensors.metrics import Types
from datetime import datetime
from typing import Dict


class Measure(object):

    def __init__(self: Measure, time: datetime, idsensor: str, metric: Types, data: float):
        self.time: datetime = time
        self.idsensor: str = idsensor
        self.metric: Types = metric
        self.data: float = data

    def __str__(self: Measure) -> str:
        return f"Measure taken at {self.time} by {self.idsensor} of {self.metric} = {self.data}"

    def sql_value(self: Measure) -> Dict[str, object]:
        return {
                'time': self.time,
                'idsensor': self.idsensor,
                'metric': self.metric.name,  # Here we handle enum to str conversion
                'data': self.data
               }
