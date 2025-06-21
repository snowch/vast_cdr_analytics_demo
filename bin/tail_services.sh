#!/bin/bash

# Usage: ./tail_services.sh [i | g | d | a]
#
# This script tails the logs of the specified service.
# If no service name is provided, it tails the logs of all services.
#
# Available services:
#   telco_demo_vast-init-db (b=dbinit)
#   telco_demo_vast-init (i=init)
#   telco_demo_telco-generator (g=gen)
#   telco_demo_vast-db-sink (d=db)

VAST_INIT_DB="telco_demo_vast-init-db"
VAST_INIT_KAFKA="telco_demo_vast-init-kafka"
TELCO_GENERATOR="telco_demo_telco-generator"
VAST_DB_SINK="telco_demo_vast-db-sink"

# Check if a service is provided as a parameter
if [ -n "$1" ]; then
  service="$1"
else
  read -p "Enter service to tail (i=init-db, k=init-kafka, g=generator, d=db_sink, a=all, Enter=all): " service
  service=${service:-a}
fi

case "$service" in
  "i")
    echo "Tailing $VAST_INIT_DB logs:"
    docker service logs -f $VAST_INIT_DB
    ;;
  "k")
    echo "Tailing $VAST_INIT_KAFKA logs:"
    docker service logs -f $VAST_INIT_KAFKA
    ;;
  "g")
    echo "Tailing $TELCO_GENERATOR logs:"
    docker service logs -f $TELCO_GENERATOR
    ;;
  "d")
    echo "Tailing $VAST_DB_SINK logs:"
    docker service logs -f $VAST_DB_SINK
    ;;
  "a")
    echo "Tailing all services:"
    docker service logs -f $VAST_INIT_DB &
    docker service logs -f $VAST_INIT_KAFKA &
    docker service logs -f $TELCO_GENERATOR &
    docker service logs -f $VAST_DB_SINK &
    wait
    ;;
  *)
    echo "Invalid service name: $service"
    echo "Usage: ./tail_services.sh [i | g | d | a]"
    exit 1
    ;;
esac
