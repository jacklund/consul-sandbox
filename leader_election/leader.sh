#! /bin/bash

host=${1:-localhost}
key="http://${host}:8500/v1/kv/service/leader_test/leader"

create_session() {
  curl -s -X PUT -d '{"Name": "leader_test"}' "http://${host}:8500/v1/session/create" | jq -r .ID
}

# Get our session ID
session_id=$(create_session)

acquire() {
  curl -s -X PUT -d '{"Name": "leader_test}' "${key}?acquire=${session_id}"
}

release() {
  echo "Releasing lock"
  curl -s -X PUT "${key}?release=${session_id}" > /dev/null 2>&1
}

release_and_exit() {
  release
  exit 0
}

wait_for_release() {
  index=$(curl -s "${key}" | jq '.[0].ModifyIndex')
  curl -s "${key}?index=${index}" > /dev/null 2>&1
}

trap release_and_exit EXIT SIGTERM SIGINT

while true; do
  lock_acquired=$(acquire)

  if [[ $lock_acquired = "true" ]]; then
    echo "I'm the leader!!!"

    # Sleep a random time between 0 and 10 seconds
    sleep $[ ( $RANDOM % 10 ) + 1 ]

    # Release the lock
    release
  else
    wait_for_release
  fi
done
