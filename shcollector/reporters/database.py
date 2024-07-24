from __future__ import annotations
from queue import Queue
import sys
import logging
from psycopg2 import DatabaseError
from psycopg2._psycopg import connection
import psycopg2
from manager import Manager
from sensors.metrics import Types
from sensors.measure import Measure
import cfg

logger = logging.getLogger("database")


class Database():

    def __init__(self: Database, measure_queue: Queue[Measure]):
        self.schema = cfg.config.get('Database', 'schema')
        self.add_sensordata = (
            "INSERT INTO " + self.schema + ".sensors_data "
            " (time, idsensor, metric, data, location) "
            " VALUES (%(time)s, %(idsensor)s, %(metric)s, %(data)s, %(location)s)"
            ";")
        self.add_sensor = (
            "INSERT INTO " + self.schema + ".sensors"
            "  VALUES (%(database_id)s, %(name)s, %(location)s)"
            "  ON CONFLICT (idsensor) DO "
            "       UPDATE SET name=excluded.name,"
            "                  current_location=excluded.current_location"
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

        # Log the error
        if hasattr(error, 'pgerror') and error.pgerror is not None:
            logger.error(f"[{error.pgcode}] {error_name} on line number {line_num} :"
                         f"\n{error.pgerror} ")
        else:
            logger.error(error)

    def check_structure(self: Database) -> None:
        try:
            logger.info("connecting to database to update table structure")
            db_connection: connection = psycopg2.connect(cfg.config.postgres_dsn())
            with db_connection.cursor() as db_cursor:

                TABLES = {}
                TABLES['sensors'] = (
                    "CREATE TABLE IF NOT EXISTS " + self.schema + ".sensors ("
                    "  \"idsensor\" text PRIMARY KEY,"
                    "  \"name\" text NOT NULL,"
                    "  \"current_location\" text"
                    ");")
                TABLES['sensors_data'] = (
                    "CREATE TABLE IF NOT EXISTS " + self.schema + ".sensors_data ("
                    "  \"time\" timestamp  with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                    "  \"idsensor\" text REFERENCES " + self.schema + ".sensors,"
                    "  \"metric\" text not null,"
                    "  \"data\" real NOT NULL,"
                    "  \"location\" text NOT NULL,"
                    "  PRIMARY KEY (time, idsensor, metric)"
                    ");")

                for name, ddl in TABLES.items():
                    logger.debug(f"Checking table {name}")
                    db_cursor.execute(ddl)
                db_connection.commit()
            db_connection.close()
        except psycopg2.DatabaseError as error:
            Database.log_psycopg2_exception(error)

    def check_sensors_definition(self: Database, manager: Manager) -> None:
        try:
            logger.info("connecting to database to update sensors definition")
            db_connection: connection = psycopg2.connect(cfg.config.postgres_dsn())
            with db_connection.cursor() as db_cursor:

                for sensor in manager.sensors.values():
                    definition = sensor.get_sensor_definition()
                    logger.debug(f"Checking sensor {definition.database_id}")
                    db_cursor.execute(self.add_sensor, vars(definition))
                db_connection.commit()
            db_connection.close()
        except psycopg2.DatabaseError as error:
            Database.log_psycopg2_exception(error)

    def write_measures(self: Database) -> None:
        success: bool = True
        try:
            # Open connection
            logger.debug("connecting to database to write measures...")
            db_connection: connection = psycopg2.connect(cfg.config.postgres_dsn())
            with db_connection.cursor() as db_cursor:

                while not self.measure_queue.empty():
                    measure: Measure = self.measure_queue.get()
                    success = False
                    if measure.metric == Types.BATTERY:
                        continue
                    logger.debug(f"Write measure {measure}")
                    db_cursor.execute(self.add_sensordata, measure.sql_value())
                    success = True

                # Make sure data is committed to the database
                db_connection.commit()
            db_connection.close()
            logger.debug("Done writing measures !")
        except psycopg2.DatabaseError as error:
            Database.log_psycopg2_exception(error)
        finally:
            # Handle exception during database write
            if success is False:
                self.measure_queue.put(measure)
