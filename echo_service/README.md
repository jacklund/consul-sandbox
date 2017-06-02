# Adding a Service

Once you [bring up your Consul cluster](../README.md#starting-up-your-cluster"), you can bring up an external service registered with it like so:

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
