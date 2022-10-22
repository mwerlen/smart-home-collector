from __future__ import annotations
from sensors.metrics import Types
from datetime import datetime
from typing import Dict


class Measure(object):

    def __init__(self: Measure, time: datetime, database_id: str, metric: Types, data: float):
        self.time: datetime = time
        self.database_id: str = database_id
        self.metric: Types = metric
        self.data: float = data

    def __str__(self: Measure) -> str:
        return f"Measure taken at {self.time} by {self.database_id} of {self.metric} = {self.data}"

    def sql_value(self: Measure) -> Dict[str, object]:
        return {
                'time': self.time,
                'idsensor': self.database_id,
                'metric': self.metric.name,  # Here we handle enum to str conversion
                'data': self.data
               }

    def get_cache_key(self: Measure) -> int:
        return hash((self.database_id, self.metric))
