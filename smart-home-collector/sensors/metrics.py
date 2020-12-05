from __future__ import annotations
from enum import Enum


class Types(Enum):
    TEMPERATURE = "Température"
    HUMIDITE = "Humidité"
    BATTERY = "Batterie"

    def __str__(self: Types) -> str:
        return self.name
