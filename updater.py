#!/usr/bin/python
# Original Script by Michael Shepanski (2013-08-01, python 2)
# Updated to work with Python 3
# Updated to use Digital Oean API v2

import json, re
import urllib.request
from datetime import datetime
import argparse
import socket

#Parse the command line arguments (all required or else exception will be thrown)
parser = argparse.ArgumentParser()
parser.add_argument("token")
parser.add_argument("domain")
parser.add_argument("record")
args = parser.parse_args()

#assign the parsed args to their respective variables
TOKEN = args.token
DOMAIN = args.domain
RECORD = args.record

APIURL = "https://api.digitalocean.com/v2"
AUTH_HEADER = {'Authorization': "Bearer %s" % (TOKEN)}

def get_local_ip():
    """ Return the current local IP. """
    print ("Fetching local IP")

    """ Get the IP that internet connections go through """
    local_ip = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    print ("Found local IP: ", local_ip)
    return local_ip

def get_domain(name=DOMAIN):
    print ("Fetching Domain ID for:", name)
    url = "%s/domains" % (APIURL)

    req = urllib.request.Request(url, headers=AUTH_HEADER)
    fp = urllib.request.urlopen(req)
    mybytes = fp.read()
    html = mybytes.decode("utf8")

    result = json.loads(html)

    for domain in result['domains']:
        if domain['name'] == name:
            return domain
    raise Exception("Could not find domain: %s" % name)

def get_record(domain, name=RECORD):
    print ("Fetching Record ID for: ", name)
    url = "%s/domains/%s/records" % (APIURL, domain['name'])
    
    def fetch_id(url):
        req = urllib.request.Request(url, headers=AUTH_HEADER)
        fp = urllib.request.urlopen(req)
        mybytes = fp.read()
        html = mybytes.decode("utf8")
        result = json.loads(html)
        
        for record in result['domain_records']:
            if record['type'] == 'A' and record['name'] == name:
                return record
 
        if result['links']['pages']['next']:
            return fetch_id(result['links']['pages']['next'])

        raise Exception("Could not find record: %s" % name)

    return fetch_id(url)

def set_record_ip(domain, record, ipaddr):
    print ("Updating record", record['name'], ".", domain['name'], "to", ipaddr)

    url = "%s/domains/%s/records/%s" % (APIURL, domain['name'], record['id'])
    data = json.dumps({'data' : ipaddr}).encode('utf-8')
    headers = {'Content-Type': 'application/json'}
    headers.update(AUTH_HEADER)

    req = urllib.request.Request(url, data, headers, method='PUT')
    fp = urllib.request.urlopen(req)
    mybytes = fp.read()
    html = mybytes.decode("utf8")
    result = json.loads(html)

    if result['domain_record']['data'] == ipaddr:
        print ("Success")


if __name__ == '__main__':
    try:
        print ("Updating ", RECORD, ".", DOMAIN, ":", datetime.now())
        ipaddr = get_local_ip()
        domain = get_domain()
        record = get_record(domain)
        if record['data'] == ipaddr:
            print ("Record %s.%s already set to %s." % (record['name'], domain['name'], ipaddr))
        else:
            set_record_ip(domain, record, ipaddr)
    except (Exception) as err:
        print ("Error: ", err)
