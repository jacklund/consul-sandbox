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

## Adding a Service

Once you bring up your Consul cluster, you can bring up an external service registered with it like so:

```bash
$ cd echo_service
$ ./run.sh
```

This will bring up the [Hashicorp echo server](https://hub.docker.com/r/hashicorp/http-echo/), which simply echoes "hello world" when you do an HTTP Get against it.
The run script registers the service with Consul, and deregisters it when it exits.

Once it's up, you should see something like this after a moment or two:

```
$ ./run.sh
Starting echoservice_echo_1 ...
Starting echoservice_echo_1 ... done
Attaching to echoservice_echo_1
echo_1  | 2017/05/31 14:24:51 Server is listening on :5678
echo_1  | 2017/05/31 14:24:54 echoservice_echo_1:5678 172.18.0.3:47370 "GET / HTTP/1.1" 200 12 "Consul Health Check" 21.874µs
echo_1  | 2017/05/31 14:25:04 echoservice_echo_1:5678 172.18.0.3:47378 "GET / HTTP/1.1" 200 12 "Consul Health Check" 9.288µs
```

Those last are the Consul cluster hitting its "health check" to make sure it's healthy. Now, you can do the following:

```bash
$ dig @localhost -p 8600 echo.service.consul ANY

; <<>> DiG 9.8.3-P1 <<>> @localhost -p 8600 echo.service.consul ANY
; (3 servers found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 16695
;; flags: qr aa rd; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0
;; WARNING: recursion requested but not available

;; QUESTION SECTION:
;echo.service.consul.           IN      ANY

;; ANSWER SECTION:
echo.service.consul.    0       IN      A       127.0.0.1

;; Query time: 1 msec
;; SERVER: 127.0.0.1#8600(127.0.0.1)
;; WHEN: Wed May 31 09:26:16 2017
;; MSG SIZE  rcvd: 53
```

i.e. the service is registered with Consul's DNS. You can also use the HTTP API:

```bash
$ curl -s localhost:8500/v1/agent/services | jq .
{
  "echo": {
    "ID": "echo",
    "Service": "echo",
    "Tags": [
      "primary",
      "v1"
    ],
    "Address": "127.0.0.1",
    "Port": 5678,
    "EnableTagOverride": false,
    "CreateIndex": 0,
    "ModifyIndex": 0
  }
}
```

If you look at http://localhost:8500 as well, you should see the service defined in the UI.
