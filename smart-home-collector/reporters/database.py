from __future__ import annotations
from typing import Dict
from queue import Queue
import sys
# import traceback
import psycopg2  # type: ignore
import psycopg2.errorcodes  # type: ignore
from sensors.manager import Manager
from sensors.metrics import Types
from sensors.measure import Measure


class Database():

    def __init__(self: Database, config: Dict, db_config: Dict, measure_queue: Queue):
        self.db_config = db_config
        self.config = config
        self.add_sensordata = (
            "INSERT INTO " + config['schema'] + ".sensors_data "
            " (time, idsensor, metric, data) "
            " VALUES (%(time)s, %(idsensor)s, %(metric)s, %(data)s)"
            ";")
        self.add_sensor = (
            "INSERT INTO " + self.config['schema'] + ".sensors"
            "  VALUES (%(idsensor)s, %(name)s, %(location)s)"
            "  ON CONFLICT (idsensor) DO "
            "       UPDATE SET name=excluded.name,"
            "                  location=excluded.location"
            ";")
        self.measure_queue = measure_queue

    @staticmethod
    def print_psycopg2_exception(error):
        # get details about the exception
        error_type, error_obj, stacktrace = sys.exc_info()

        # get the line number when exception occured
        line_num = stacktrace.tb_lineno

        # print the connect() error
        print(f"\n[{error.pgcode}] {error_type.__name__} on line number {line_num} :"
              f"\n{error.pgerror} ")

        # if config['debug']:
        #   traceback.print_tb(stacktrace)
        #   print(f"\nextensions.Diagnostics: {str(error.diag)}")

    def check_structure(self: Database):
        try:
            print("Connecting to database to update table structure")
            connection = psycopg2.connect(**self.db_config)
            cursor = connection.cursor()

            TABLES = {}
            TABLES['sensors'] = (
                "CREATE TABLE IF NOT EXISTS " + self.config['schema'] + ".sensors ("
                "  \"idsensor\" text PRIMARY KEY,"
                "  \"name\" text NOT NULL,"
                "  \"location\" text"
                ");")
            TABLES['sensors_data'] = (
                "CREATE TABLE IF NOT EXISTS " + self.config['schema'] + ".sensors_data ("
                "  \"time\" timestamp  with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,"
                "  \"idsensor\" text REFERENCES " + self.config['schema'] + ".sensors,"
                "  \"metric\" text not null,"
                "  \"data\" real NOT NULL,"
                "  PRIMARY KEY (time, idsensor, metric)"
                ");")

            for name, ddl in TABLES.items():
                print(f"Checking table {name}")
                cursor.execute(ddl)
            connection.commit()
            cursor.close()
            connection.close()
        except psycopg2.DatabaseError as error:
            Database.print_psycopg2_exception(error)

    def check_sensors_definition(self: Database, manager: Manager):
        try:
            print("Connecting to database to update sensors definition")
            connection = psycopg2.connect(**self.db_config)
            cursor = connection.cursor()

            for sensor in manager.sensors:
                definition = sensor.get_sensor_definition()
                print(f"Checking sensor {definition.idsensor}")
                cursor.execute(self.add_sensor, vars(definition))
            connection.commit()
            cursor.close()
            connection.close()
        except psycopg2.DatabaseError as error:
            Database.print_psycopg2_exception(error)

    def write_measures(self: Database):
        try:
            # Open connection
            print("Connecting to database to write measures...")
            connection = psycopg2.connect(**self.db_config)
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
            print("Done !")
        except psycopg2.DatabaseError as error:
            Database.print_psycopg2_exception(error)
