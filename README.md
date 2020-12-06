RTL_433 sensors' value collector
================================

This projects aims to collect data from 433 MHz sensors (thermometer, hygrometer...).


To-do list
----------

* Add a shlex parser to allow simpler debug and specify a configuration file
* Change cron-style scheduler and remove scheduler from global variables
* Add unit tests (next run computing, close_all..)
* Create a "domotic" or "Home automation" or "Smart Home" role in Ansible to provision it on server
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
