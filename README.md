# Sandbox for Testing a Consul Cluster using Docker

This is a basic [docker compose](https://docs.docker.com/compose/) setup which brings up a 3-server [Consul](https://www.consul.io) cluster that you can interact with, using Docker.

You'll need a [docker](https://docker.com) environment set up on your machine - installation instructions [here](https://docs.docker.com/engine/installation/).
Under Mac OS (which is where I ran my tests) you'll need to install and start [Docker for Mac](https://docs.docker.com/docker-for-mac/).

## Starting Up Your Cluster

To start up your cluster, run:

```bash
$ docker-compose up -d
```

This will start up three Consul servers and one client in the background, and bootstrap them into a cluster. If you point your browser to
http://localhost:8500, you will see the nifty Consul UI showing you the nodes in your cluster.

If you install Consul locally onto your machine, you can use the Consul CLI to query your cluster. For instance, if you do

```bash
$ consul members
```

you should see something like this:

```bash
Node          Address          Status  Type    Build  Protocol  DC
2aae8df1a765  172.18.0.2:8301  alive   server  0.8.3  2         dc1
342a030e7733  172.18.0.4:8301  alive   server  0.8.3  2         dc1
961968db746d  172.18.0.5:8301  alive   client  0.8.3  2         dc1
ec356ee41dc7  172.18.0.3:8301  alive   server  0.8.3  2         dc1
```

You can query the RAFT membership as well:

```bash
$ consul operator raft list-peers
Node          ID               Address          State     Voter  RaftProtocol
2aae8df1a765  172.18.0.2:8300  172.18.0.2:8300  leader    true   2
342a030e7733  172.18.0.4:8300  172.18.0.4:8300  follower  true   2
ec356ee41dc7  172.18.0.3:8300  172.18.0.3:8300  follower  true   2
```

## Cluster Details

This sets up a 3-server Consul cluster, with a non-server agent running to handle the UI and CLI requests. The way it bootstraps is
it brings up the first server node first, and then has all the rest of the nodes join that node. Once the cluster is bootstrapped, they
all talk to one another using the Gossip protocol, so you're not dependant on the first server being up any more - new nodes can join
by communicating with any live node that is part of the cluster.

## Fun Tricks for your Cluster

If you're interested in playing with the cluster, you can, for instance, kill one of the nodes (using the `docker kill <container-id>` command), and then
you should see the following (after a minute or so - it takes a little while for the cluster to figure out one of the nodes is down):

```bash
$ consul members
Node          Address          Status  Type    Build  Protocol  DC
2aae8df1a765  172.18.0.2:8301  failed  server  0.8.3  2         dc1
342a030e7733  172.18.0.4:8301  alive   server  0.8.3  2         dc1
961968db746d  172.18.0.5:8301  alive   client  0.8.3  2         dc1
ec356ee41dc7  172.18.0.3:8301  alive   server  0.8.3  2         dc1

$ consul operator raft list-peers
Node          ID               Address          State     Voter  RaftProtocol
2aae8df1a765  172.18.0.2:8300  172.18.0.2:8300  follower  true   2
342a030e7733  172.18.0.4:8300  172.18.0.4:8300  leader    true   2
ec356ee41dc7  172.18.0.3:8300  172.18.0.3:8300  follower  true   2
```

Notice that the `consul members` shows the node as failed, but `list-peers` still shows it as part of the cluster. That's because the Raft consensus protocol won't remove it from
the Raft cluster until a timeout has passed (the default is 72 hours, but is [configurable](https://www.consul.io/docs/agent/options.html#reconnect_timeout)). You can, however, manually
remove a node using `consul force-leave <id>`, like so:

```bash
$ consul members
Node          Address          Status  Type    Build  Protocol  DC
2aae8df1a765  172.18.0.2:8301  failed  server  0.8.3  2         dc1
342a030e7733  172.18.0.4:8301  alive   server  0.8.3  2         dc1
961968db746d  172.18.0.5:8301  alive   client  0.8.3  2         dc1
ec356ee41dc7  172.18.0.3:8301  alive   server  0.8.3  2         dc1

$ consul operator raft list-peers
Node          ID               Address          State     Voter  RaftProtocol
2aae8df1a765  172.18.0.2:8300  172.18.0.2:8300  follower  true   2
342a030e7733  172.18.0.4:8300  172.18.0.4:8300  leader    true   2
ec356ee41dc7  172.18.0.3:8300  172.18.0.3:8300  follower  true   2

$ consul force-leave 2aae8df1a765

$ consul members
Node          Address          Status  Type    Build  Protocol  DC
2aae8df1a765  172.18.0.2:8301  left    server  0.8.3  2         dc1
342a030e7733  172.18.0.4:8301  alive   server  0.8.3  2         dc1
961968db746d  172.18.0.5:8301  alive   client  0.8.3  2         dc1
ec356ee41dc7  172.18.0.3:8301  alive   server  0.8.3  2         dc1

$ consul operator raft list-peers
Node          ID               Address          State     Voter  RaftProtocol
342a030e7733  172.18.0.4:8300  172.18.0.4:8300  leader    true   2
ec356ee41dc7  172.18.0.3:8300  172.18.0.3:8300  follower  true   2
```

You can then add a new node to your cluster to get it back up to three. You can either do:

```bash
$ docker-compose up -d
```

which will bring up another node with the same hostname as the one you took down (simulating the same node coming back online), or

```bash
$ docker-compose -f docker-compose-server4.yml up -d
```

which will bring up a different node with a different node ID and hostname (to simulate the node being replaced by another node, e.g. in AWS).

## Other Things You Can Do

- [Add a service](./echo_service/README.md)
- [Test leader election](./leader_election/README.md)
