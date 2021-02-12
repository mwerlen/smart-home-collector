RTL_433 sensors' value collector
================================

This projects aims to collect data from sensors (thermometer, hygrometer...) through a 
433 MHz antenna. Collected data are then inserted in a PostgreSQL database.
This script also store in files the battery status of sensors to be check by a monitoring system.


To-do list
----------

* Add unit tests (next run computing, close_all..)
* Use two reporter (one for file/battery) and uses an accept function to dispatch measures


Architecture
------------

Modules:
* Main : Initialize other modules and parse command line options
* SDR : Spawn RTL433 and read periodically
* Sensors : Handle sensors messages (radio signal) and transformation it into measure object
* Manager : Receives messages, dispatch it to specialized classes and get measures back at regular interval
* Database : Stores measures to database
* Config : retrieves parameters from configuration file and makes them available to other modules
* Cron & Job : Schedule jobs by cron-like expressions


Database schema
---------------

![Database schema](database_schema.svg?raw=true "Database schema")

[modeline]: # ( vim: set spelllang=en: )
