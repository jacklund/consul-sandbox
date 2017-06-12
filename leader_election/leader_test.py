#!/usr/bin/env python

import argparse
import requests
import socket
import sys
import threading
import time

KEY = "/kv/service/leader_test/leader"

def log(value):
    sys.stderr.write(str(value) + '\n')

class TCPHealthCheck(threading.Thread):
    def __init__(self, port):
        super(TCPHealthCheck, self).__init__()
        self.port = port

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(('', self.port))
        except socket.error as msg:
            log('Bind failed: {}'.format(msg[1]))

        s.listen(10)

        while True:
            conn, addr = s.accept()
            conn.close()

class TTLHealthCheck(threading.Thread):
    def __init__(self, base_url, interval):
        super(TTLHealthCheck, self).__init__()
        self.interval = interval
        self.base_url = base_url

    def run(self):
        while True:
            log('sending TTL ping')
            requests.get(self.base_url + '/agent/check/pass/leader_check')
            time.sleep(self.interval - 1)

def start_health_check(base_url, port, ttl):
    log('Starting health check thread')
    if port:
        TCPHealthCheck(port).start()
    if ttl:
        TTLHealthCheck(base_url, ttl).start()

def setup_debug():
    import httplib as http_client
    import logging
    http_client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

def create_session(base_url, tcp, ttl):
    data = { 'Name': 'leader_test' }
    if tcp or ttl:
        data['Checks'] = [ 'leader_check', 'serfHealth' ]
    response = requests.put(base_url + '/session/create', json=data)
    response.raise_for_status()
    return response.json()['ID']

def register_health_check(base_url, ip_address, health_check_port, ttl_interval):
    data = {
            'Name': 'leader_check',
            'Interval': '10s'
           }

    if health_check_port:
        data['TCP'] = '{}:{}'.format(ip_address, health_check_port)

    if ttl_interval:
        data['TTL'] = '{}s'.format(ttl_interval)

    log('registering health check with ' + str(data))
    response = requests.put(base_url + '/agent/check/register', json=data)
    response.raise_for_status()

def wait_for_health_check(base_url, check_name):
    log('waiting for health check')
    status = 'critical'
    while True:
        response = requests.get(base_url + '/agent/checks')
        response.raise_for_status()
        json = response.json()
        for key in json:
            value = json[key]
            if value['Name'] == check_name:
                status = value['Status']
                if status != 'critical':
                    log(status)
                    return
        time.sleep(1)

def acquire_leader_lock(base_url, session_id):
    data = socket.gethostname()
    query = { 'acquire': session_id }
    response = requests.put(base_url + KEY, params=query, data=data)
    response.raise_for_status()
    return response.text == 'true'

def wait_for_leader_lock(base_url):
    response = requests.get(base_url + KEY)
    response.raise_for_status()
    metadata = response.json()[0]
    log(metadata)
    session = metadata.get('Session')
    while session:
        index = metadata['ModifyIndex']
        params = { 'index': index }
        response = requests.get(base_url + KEY, params=params)
        response.raise_for_status()
        metadata = response.json()[0]
        log(metadata)
        session = metadata.get('Session')

def main():
    parser = argparse.ArgumentParser(description='Test Consul leader election')
    parser.add_argument('ip_address', help='IP address of host')
    parser.add_argument('host', help='hostname of agent to connect to', default='localhost', nargs='?')
    parser.add_argument('--tcp', metavar='PORT', help='Add TCP health check on port', type=int, nargs='?')
    parser.add_argument('--ttl', metavar='TTL', help='Add TTL health check with specified interval in seconds', type=int, nargs='?')

    args = parser.parse_args()

    log(args)

    base_url = 'http://{}:8500/v1'.format(args.host)

    # setup_debug()

    if args.tcp or args.ttl:
        start_health_check(base_url, args.tcp, args.ttl)
        register_health_check(base_url, args.ip_address, args.tcp, args.ttl)
        wait_for_health_check(base_url, 'leader_check')

    session_id = create_session(base_url, args.tcp, args.ttl)

    log(session_id)

    while True:
        start = time.time()
        am_leader = acquire_leader_lock(base_url, session_id)
        if am_leader:
            log("I'm the leader!!!")
        else:
            log("I'm a follower - waiting on leader lock")
        wait_for_leader_lock(base_url)
        end = time.time()

        # Avoid stampeding Consul with leader attempts during lock-delay
        if end - start < 1:
            log("Sleeping for 3 seconds")
            time.sleep(3)

if __name__ == '__main__':
    main()
