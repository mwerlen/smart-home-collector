from __future__ import annotations
from configparser import ConfigParser
import os
import logging

logger = logging.getLogger("config")


class Config(ConfigParser):

    def __init__(self: Config):
        ConfigParser.__init__(self, inline_comment_prefixes=('#'))
        default_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default.ini')
        self.read(default_file)
        self.apply_loggers_level()
        logger.debug(f"Loaded file {default_file} with sections {self.sections()}")

    def apply_loggers_level(self: Config) -> None:
        # Configure logging
        logging.basicConfig(level=self.get('Log', 'level'), format=self.get('Log', 'format'))

    def postgres_dsn(self: Config) -> str:
        return (f"dbname={self['Database']['database']}"
                f" user={self['Database']['user']}"
                f" password={self['Database']['password']}"
                f" host={self['Database']['host']}"
                f" port={self['Database']['port']}")

    def set_config_file(self: Config, config_file: str) -> None:
        self.read(config_file)

    def set_debug(self: Config, debug: bool) -> None:
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
