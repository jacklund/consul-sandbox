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

class HealthCheck(threading.Thread):
    def __init__(self, port):
        super(HealthCheck, self).__init__()
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

def start_health_check(port):
    log('Starting health check thread')
    HealthCheck(port).start()

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

def create_session(base_url):
    data = { 'Name': 'leader_test', 'Checks': [ 'leader_check', 'serfHealth' ] }
    # data = { 'Name': 'leader_test' }
    response = requests.put(base_url + '/session/create', json=data)
    response.raise_for_status()
    return response.json()['ID']

def register_health_check(base_url, ip_address, health_check_port):
    data = {
            'Name': 'leader_check',
            'TCP': '{}:{}'.format(ip_address, health_check_port),
            'Interval': '10s'
           }

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
    data = { 'Name': 'leader' }
    query = { 'acquire': session_id }
    response = requests.put(base_url + KEY, params=query, json=data)
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
    parser.add_argument('port', help='health check port number', type=int, nargs='?', default=5678)

    args = parser.parse_args()

    base_url = 'http://{}:8500/v1'.format(args.host)

    # setup_debug()

    start_health_check(args.port)
    register_health_check(base_url, args.ip_address, args.port)
    wait_for_health_check(base_url, 'leader_check')

    session_id = create_session(base_url)

    log(session_id)

    while True:
        am_leader = acquire_leader_lock(base_url, session_id)
        if am_leader:
            log("I'm the leader!!!")
        else:
            log("I'm a follower - waiting on leader lock")
        wait_for_leader_lock(base_url)

if __name__ == '__main__':
    main()
