# Leader Election

This tests the [leader election](https://www.consul.io/docs/guides/leader-election.html) feature in Consul. It spins up N instances, all of which
run a script to try to get leadership of their cluster using Consul. WHen one gets leadership, it tells you, then waits for a random time between
0 and 10 seconds, and then releases leadership, and someone else takes it.

There are three different flavors, each of which uses a different set of health checks for its session: one uses just the Serf health check provided
by the Consul agent running in the container, another uses a TTL-based health check, where the service sends a signal to reset a countdown timer in the
agent, and the third is a TCP-based health check, where the agent opens a connection on a given port to the service to test its health.

## Building

```bash
$ ./build.sh
```

## Running

Make sure your [Consul cluster is running](../README.md#starting-up-your-cluster), and then:

```bash
$ docker-compose up -f docker-compose-<type>.yml--scale leader_test=N
```

where <type> is one of `serf`, `tcp`, or `ttl`, and `N` is the number of instances you want (3 is a good number).

## Testing Leader Election

Once you have your instances running, one of the the instances will announce that it's the leader, and the others will tell you that they
are followers. You can take the leader down either with `docker kill`, or by shelling onto the container with `docker exec -it <container-id> /bin/sh`
and killing the `leader-test` process (or, in the case of the Serf one, just kill the agent).
