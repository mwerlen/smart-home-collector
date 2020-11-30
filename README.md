RTL_433 sensors' value collector
================================

This projects aims to collect data from 433 MHz sensors (thermometer, hygrometer...).


To-do list
----------

* Continue to split code in small modules
* Add unit tests (next run computing, close_all..)
* Add a configuration parser to read _ini_ style configuration files
* Create a "domotic" or "Home automation" or "Smart Home" role in Ansible to provision it on server
* Create an aggregation function and schedule-it (or use a queue or pub/sub)
* Replace print by a logger


Architecture
------------

Modules:
* Main : Init other modules and schedule actions
* sdr : Spawn RTL433 and read periodically
* asyncreader : The AsynchronousFileReader
* Sensors : Handle sensors information treatment and transformation in SignalData object
* Aggregator : Receives signalData and aggregates-it
* DatabaseStorage : Periodically polls Aggregator and flush data to database

[modeline]: # ( vim: set spelllang=en: )
