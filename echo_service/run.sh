#! /bin/bash

curl --request PUT --data @register.json localhost:8500/v1/agent/service/register

docker-compose up

curl --request PUT localhost:8500/v1/agent/service/deregister/echo
