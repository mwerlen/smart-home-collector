#!/bin/bash
set -euo pipefail
IFS=$'\n\t'


while /bin/true; do
    echo '{"time" : "'$(date +"%Y-%m-%d %H:%M:%S")'", "brand" : "LaCrosse", "model" : "LaCrosse-TX29IT", "id" : 7, "battery_ok" : '$(($RANDOM%2))', "newbattery" : 0, "temperature_C" : '$(date +%H.%M%S)', "mic" : "CRC"}'
    echo '{"time" : "'$(date +"%Y-%m-%d %H:%M:%S")'", "brand" : "LaCrosse", "model" : "LaCrosse-TX29IT", "id" : 0, "battery_ok" : '$(($RANDOM%2))', "newbattery" : 0, "temperature_C" : '$(date -u +%H.%M%S)', "mic" : "CRC"}'
    echo '{"time" : "'$(date +"%Y-%m-%d %H:%M:%S")'", "model" : "Thermopro-TX2C", "subtype" : 9, "id" : 69, "channel" : 2, "battery_ok" : '$(($RANDOM%2))', "temperature_C" : '$(date -u +%H.%M%S)', "humidity" : '$((($RANDOM%70)+15))', "button" : 0}'
    sleep 9
    done
