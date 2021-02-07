#!/bin/bash
set -euo pipefail
IFS=$'\n\t'


while /bin/true; do
    echo '{"time" : "'$(date +"%Y-%m-%d %H:%M:%S")'", "brand" : "LaCrosse", "model" : "LaCrosse-TX29IT", "id" : 7, "battery_ok" : '$(($RANDOM%2))', "newbattery" : 0, "temperature_C" : '$(date +%H.%M%S)', "mic" : "CRC"}'
    sleep 9
    done
