from __future__ import annotations
from enum import Enum


class Types(Enum):
    TEMPERATURE = "Température"
    HUMIDITY = "Humidité"
    BATTERY = "Batterie"

    def __str__(self: Types) -> str:
        return self.name

    def threshold(self: Types) -> int:
        if self == Types.TEMPERATURE:
            return 20
        elif self == Types.HUMIDITY:
            return 50
        else:
            return 99
