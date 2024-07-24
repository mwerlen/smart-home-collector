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
5. Modify the aggregation procedure to use the location instead of idsensor

<!-- vim: set spelllang=en: -->
