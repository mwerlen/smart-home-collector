from __future__ import annotations
from sensors.metrics import Types
from datetime import datetime
from typing import Tuple


class Measure:

    def __init__(self: Measure, time: datetime, idsensor: str, metric: Types, data: float):
        self._time = time
        self._idsensor = idsensor
        self._metric = metric
        self._data = data

    def time(self: Measure) -> datetime:
        return self._time

    def idsensor(self: Measure) -> str:
        return self._idsensor

    def metric(self: Measure) -> Types:
        return self._metric

    def data(self: Measure) -> float:
        return self._data

    def tuple(self: Measure) -> Tuple[datetime, str, Types, float]:
        return (self.time(), self.idsensor(), self.metric(), self.data())
