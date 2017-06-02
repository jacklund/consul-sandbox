# Leader Election

This tests the [leader election](https://www.consul.io/docs/guides/leader-election.html) feature in Consul. It spins up N instances, all of which
run a script to try to get leadership of their cluster using Consul. WHen one gets leadership, it tells you, then waits for a random time between
0 and 10 seconds, and then releases leadership, and someone else takes it.

## Building

```bash
$ ./build.sh
```

## Running

Make sure your [Consul cluster is running](../README.md#starting-up-your-cluster), and then:

```bash
$ docker-compose up --scale leader_test=N
```

where `N` is the number of instances you want. 3 is a good number.
