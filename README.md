RTL_433 sensors' value collector
================================

This projects aims to collect data from 433 MHz sensors (thermometer, hygrometer...).


To-do list
----------

* Split scheduler between sensor readings and data push to DB
* Add unit tests (next run computing, close_all..)
* Add a configuration parser to read _ini_ style configuration files
* Add sensors informations (id, location, metric type) and use it
* Create a "domotic" or "Home automation" or "Smart Home" role in Ansible to provision it on server
* Create an aggregation function and schedule-it

[modeline]: # ( vim: set spelllang=en: )
