RTL_433 sensors' value collector
================================

This projects aims to collect data from 433 MHz sensors (thermometer, hygrometer...).


To-do list
----------

* Add unit tests (next run computing, close_all..)
* Add a configuration parser to read _ini_ style configuration files
* Create a "domotic" or "Home automation" or "Smart Home" role in Ansible to provision it on server
* Replace print by a logger
* Use two reporter (one for file/battery) and uses an accept function to dispatch measures


Architecture
------------

Modules:
* Main : Initialize other modules and schedule actions
* SDR : Spawn RTL433 and read periodically
* Sensors : Handle sensors messages (radio signal) and transformation it into measure object
* Manager : Receives messages, dispatch it to specialized classes and get measures back at regular interval
* Database : Stores measures to database

[modeline]: # ( vim: set spelllang=en: )
