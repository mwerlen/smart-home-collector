from __future__ import annotations
from queue import Queue
import sys
import logging
from psycopg2 import DatabaseError  # type: ignore
import psycopg2
from sensors.manager import Manager
from sensors.metrics import Types
from sensors.measure import Measure
import cfg

logger = logging.getLogger("database")


class Database():

    def __init__(self: Database, measure_queue: Queue[Measure]):
        self.schema = cfg.config.get('Database', 'schema')
        self.add_sensordata = (
            "INSERT INTO " + self.schema + ".sensors_data "
            " (time, idsensor, metric, data) "
            " VALUES (%(time)s, %(idsensor)s, %(metric)s, %(data)s)"
            ";")
        self.add_sensor = (
            "INSERT INTO " + self.schema + ".sensors"
            "  VALUES (%(idsensor)s, %(name)s, %(location)s)"
            "  ON CONFLICT (idsensor) DO "
            "       UPDATE SET name=excluded.name,"
            "                  location=excluded.location"
            ";")
        self.measure_queue = measure_queue

    @staticmethod
    def log_psycopg2_exception(error: DatabaseError) -> None:
        # get details about the exception
        error_type, error_obj, stacktrace = sys.exc_info()

        # Get error_type
        if error_type is None:
            error_name = "Unkown error"
        else:
            error_name = error_type.__name__

        # get the line number when exception occured
        if stacktrace is None:
            line_num = "unknown"
        else:
            line_num = str(stacktrace.tb_lineno)

        # Log the connect() error
        logger.error(f"\n[{error.pgcode}] {error_name} on line number {line_num} :"
                     f"\n{error.pgerror} ")

    def check_structure(self: Database) -> None:
        try:
            logger.info("Connecting to database to update table structure")
            connection = psycopg2.connect(cfg.config.postgres_dsn())
            cursor = connection.cursor()

            TABLES = {}
            TABLES['sensors'] = (
                "CREATE TABLE IF NOT EXISTS " + self.schema + ".sensors ("
                "  \"idsensor\" text PRIMARY KEY,"
                "  \"name\" text NOT NULL,"
                "  \"location\" text"
                ");")
            TABLES['sensors_data'] = (
                "CREATE TABLE IF NOT EXISTS " + self.schema + ".sensors_data ("
                "  \"time\" timestamp  with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                "  \"idsensor\" text REFERENCES " + self.schema + ".sensors,"
                "  \"metric\" text not null,"
                "  \"data\" real NOT NULL,"
                "  PRIMARY KEY (time, idsensor, metric)"
                ");")

            for name, ddl in TABLES.items():
                logger.debug(f"Checking table {name}")
                cursor.execute(ddl)
            connection.commit()
            cursor.close()
            connection.close()
        except psycopg2.DatabaseError as error:
            Database.log_psycopg2_exception(error)

    def check_sensors_definition(self: Database, manager: Manager) -> None:
        try:
            logger.info("Connecting to database to update sensors definition")
            connection = psycopg2.connect(cfg.config.postgres_dsn())
            cursor = connection.cursor()

            for sensor in manager.sensors:
                definition = sensor.get_sensor_definition()
                logger.debug(f"Checking sensor {definition.idsensor}")
                cursor.execute(self.add_sensor, vars(definition))
            connection.commit()
            cursor.close()
            connection.close()
        except psycopg2.DatabaseError as error:
            Database.log_psycopg2_exception(error)

    def write_measures(self: Database) -> None:
        try:
            # Open connection
            logger.debug("Connecting to database to write measures...")
            connection = psycopg2.connect(cfg.config.postgres_dsn())
            cursor = connection.cursor()

            while not self.measure_queue.empty():
                measure: Measure = self.measure_queue.get()
                if measure.metric == Types.BATTERY:
                    continue
                cursor.execute(self.add_sensordata, measure.sql_value())

            # Make sure data is committed to the database
            connection.commit()
            cursor.close()
            connection.close()
            logger.debug("Done writing measures !")
        except psycopg2.DatabaseError as error:
            Database.log_psycopg2_exception(error)
