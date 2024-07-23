Allow sensors to be moved
=========================

Goal
----

The goal is to allow a sensor to be moved with only a change in the configuration file.
A line in the sensor table must be long lived. When a sensor is moved we do not need to
update all the sensor_data.


How to do 
---------

* stop shcollector
* psql - Add a nullable field location to the table sensor_data
* psql - Update the location field based on the sensor
* psql - Make the field non nullable
* psql - Rename the field location of the sensor table to current_location
* database.py - Add a field location to the table sensor_data
* database.py - Rename the field location of the sensor table to current_location
* sensors/Measure - add a field location in constructor, \_\_str\_\_ and SQL value
* sensors/\* - modify each sensor type to include location in measures
* database.py - add the location when adding lines in the sensor_data
* Edit config to adapt the location to smaller codes
* Restart shcollector and check log
* Adapt the grafana dashboards' requests

Why
---

* No location table : not yet. It may be interesting at some time, but let keep it simple.
* Have a sensor table with multiple line per actual sensor for each location (2 lines if a
sensor has been moved once). It's easier to adapt the existing code, but harder to follow
the sensors.


Rename the sensors
==================

Rationale
---------

Current sensors have id witch combine types and location. We aim to remove location from
the sensors.


How to proceed
--------------

1. Mark a number (#1, #2...) on similar sensors (ThermoPro)
2. Change the shcollector configuration file to insert new sensors definition in the sensor
table. These new lines must have the type and a number (ThermoPro #1...)
3. Using psql edit all the existing lines in sensor data to change the idsensor from old
values to the newly created sensor lines.
4. Remove old sensors lines

<!-- vim: set spelllang=en: -->
