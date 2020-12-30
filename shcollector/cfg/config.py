from __future__ import annotations
from configparser import ConfigParser
import os
import logging
import logging.handlers

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
        if 'logfile' in self['Log'] and len(self['Log']['logfile']) > 0:
            logging.debug(f"Log file configured : {self['Log']['logfile']}")
            file_handler = logging.handlers.WatchedFileHandler(self.get('Log', 'logfile'))
            file_handler.setFormatter(logging.Formatter(self.get('Log', 'format')))
            logging.getLogger().addHandler(file_handler)

    def postgres_dsn(self: Config) -> str:
        dsn = f"dbname={self['Database']['database']}"
        dsn += f" user={self['Database']['user']}"
        dsn += f" host={self['Database']['host']}"
        dsn += f" port={self['Database']['port']}"

        if 'password' in self['Database'] and len(self['Database']['password']) > 0:
            dsn += f" password={self['Database']['password']}"

        return dsn

    def set_config_file(self: Config, config_file: str) -> None:
        self.read(config_file)
        self.apply_loggers_level()
        logger.debug(f"Loaded file {config_file} with sections {self.sections()}")
        logger.info(f"New postgres dsn : {self.postgres_dsn()}")


    def set_debug(self: Config, debug: bool) -> None:
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Log level is now debug")
