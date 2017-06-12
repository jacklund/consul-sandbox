#! /bin/sh

ip_address=$(ifconfig eth0 | grep inet | awk '{ print $2 }' | sed 's/addr://')
port=5678

# start_health_check() {
#   while true; do
#     echo -n | nc -l -p $port
#   done &
# }

start_consul_agent() {
  /usr/local/bin/docker-entrypoint.sh agent -raft-protocol 3 -node-id $(uuidgen) -join consulsandbox_server1_1 &
}

# start_health_check

start_consul_agent

# sleep 10

/usr/local/bin/leader_test localhost $@ & # $ip_address

sleep 999999
